"""
services/rag/retriever.py — Hybrid + MMR Retrieval

Implements a production retrieval stack:

  HybridRetriever  — Combines BM25 keyword scoring (sparse) with cosine
                     similarity (dense) using a configurable alpha weight.
  MMRRetriever     — Applies Maximum Marginal Relevance on top of hybrid
                     results to maximise diversity while preserving relevance.
  FilteredRetriever — Timestamp- and topic-aware pre-filter before retrieval.

Issue Resolved: #4 (retrieval layer undefined — no MMR, hybrid search, filtering)
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.config import settings
from services.rag.embedding_store import EmbeddingStore, embedding_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BM25 scoring (in-process, no external dependency)
# ---------------------------------------------------------------------------

class BM25:
    """Lightweight BM25 implementation using pure Python + Counter."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._corpus: List[List[str]] = []
        self._idf: Dict[str, float] = {}
        self._avg_dl: float = 0.0

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        stopwords = {
            "the", "a", "an", "is", "it", "in", "on", "at", "of", "and",
            "to", "for", "this", "that", "we", "you", "i", "are", "was",
            "with", "as", "by", "be", "from", "but", "not", "or", "so",
        }
        return [
            w.lower()
            for w in re.findall(r"\w+", text)
            if w.lower() not in stopwords and len(w) > 2
        ]

    def fit(self, documents: List[str]) -> None:
        self._corpus = [self._tokenize(d) for d in documents]
        n = len(self._corpus)
        self._avg_dl = sum(len(d) for d in self._corpus) / max(n, 1)

        df: Counter = Counter()
        for doc in self._corpus:
            df.update(set(doc))

        self._idf = {
            term: math.log((n - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def score(self, query: str, doc_idx: int) -> float:
        tokens = self._tokenize(query)
        doc = self._corpus[doc_idx]
        dl = len(doc)
        tf_map = Counter(doc)
        score = 0.0
        for t in tokens:
            if t not in tf_map:
                continue
            idf = self._idf.get(t, 0.0)
            tf = tf_map[t]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / self._avg_dl)
            score += idf * numerator / denominator
        return score

    def scores(self, query: str) -> List[float]:
        return [self.score(query, i) for i in range(len(self._corpus))]


# ---------------------------------------------------------------------------
# Cosine similarity helper
# ---------------------------------------------------------------------------

def _cosine(a: List[float], b: List[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# HybridRetriever
# ---------------------------------------------------------------------------

class HybridRetriever:
    """
    Blends BM25 keyword score (sparse) with cosine similarity (dense).

    hybrid_score = alpha * bm25_norm + (1 - alpha) * cosine
    """

    def __init__(
        self,
        store: EmbeddingStore = embedding_store,
        bm25_alpha: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> None:
        self._store = store
        self.bm25_alpha = bm25_alpha if bm25_alpha is not None else settings.HYBRID_BM25_ALPHA
        self.top_k = top_k or settings.TOP_K_RESULTS

    def _normalize(self, scores: List[float]) -> List[float]:
        mn, mx = min(scores), max(scores)
        if mx == mn:
            return [0.0] * len(scores)
        return [(s - mn) / (mx - mn) for s in scores]

    async def retrieve(
        self,
        video_id: str,
        query: str,
        query_embedding: List[float],
        *,
        top_k: Optional[int] = None,
        filter_start: Optional[float] = None,
        filter_end: Optional[float] = None,
        filter_topic: Optional[str] = None,
        filter_source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return top-k chunks ranked by hybrid BM25 + cosine score.

        Optional filters (applied before scoring):
          filter_start / filter_end  — timestamp window (seconds)
          filter_topic               — exact topic name match
          filter_source              — "transcript" | "ocr" | "fused"
        """
        k = top_k or self.top_k
        records = self._store.get_records(video_id)
        if not records:
            logger.warning("HybridRetriever: no records found for video %s", video_id)
            return []

        # Apply metadata filters
        if filter_start is not None:
            records = [r for r in records if (r.get("end_time") or 0) >= filter_start]
        if filter_end is not None:
            records = [r for r in records if (r.get("start_time") or 0) <= filter_end]
        if filter_topic:
            records = [r for r in records if r.get("topic") == filter_topic]
        if filter_source:
            records = [r for r in records if r.get("source") == filter_source]

        if not records:
            return []

        texts = [r["text"] for r in records]

        # Dense scores
        dense_scores: List[float] = []
        for r in records:
            emb = r.get("embedding")
            if emb:
                dense_scores.append(_cosine(query_embedding, emb))
            else:
                dense_scores.append(0.0)

        # Sparse BM25 scores
        bm25 = BM25()
        bm25.fit(texts)
        sparse_scores = bm25.scores(query)

        # Normalise both to [0, 1]
        dense_norm = self._normalize(dense_scores)
        sparse_norm = self._normalize(sparse_scores)

        # Blend
        hybrid_scores = [
            self.bm25_alpha * s + (1 - self.bm25_alpha) * d
            for s, d in zip(sparse_norm, dense_norm)
        ]

        # Rank
        ranked = sorted(
            zip(records, hybrid_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {**rec, "score": score, "score_type": "hybrid"}
            for rec, score in ranked[:k]
        ]


# ---------------------------------------------------------------------------
# MMRRetriever — Maximum Marginal Relevance
# ---------------------------------------------------------------------------

class MMRRetriever:
    """
    Wraps HybridRetriever and applies MMR to promote diverse results.

    MMR formula:
        score = lambda * relevance(d, q) - (1 - lambda) * max_sim(d, S)

    Where S is the set of already-selected chunks.
    MMR_LAMBDA=1.0 → pure relevance; MMR_LAMBDA=0.0 → pure diversity.
    """

    def __init__(
        self,
        hybrid: Optional[HybridRetriever] = None,
        mmr_lambda: Optional[float] = None,
        top_k: Optional[int] = None,
        fetch_k: int = 20,  # how many candidates to fetch before MMR
    ) -> None:
        self._hybrid = hybrid or HybridRetriever()
        self.mmr_lambda = mmr_lambda if mmr_lambda is not None else settings.MMR_LAMBDA
        self.top_k = top_k or settings.RERANK_TOP_N
        self.fetch_k = fetch_k

    async def retrieve(
        self,
        video_id: str,
        query: str,
        query_embedding: List[float],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        # Step 1: Get larger candidate set
        candidates = await self._hybrid.retrieve(
            video_id,
            query,
            query_embedding,
            top_k=self.fetch_k,
            **kwargs,
        )

        if len(candidates) <= self.top_k:
            return candidates

        # Step 2: MMR selection
        selected: List[Dict] = []
        remaining = list(candidates)

        while remaining and len(selected) < self.top_k:
            best_score = -1.0
            best_idx = 0

            for i, cand in enumerate(remaining):
                relevance = cand.get("score", 0.0)
                cand_emb = cand.get("embedding")

                if selected and cand_emb:
                    # Penalise redundancy: similarity to already-selected chunks
                    max_sim = max(
                        _cosine(cand_emb, s.get("embedding", []))
                        for s in selected
                        if s.get("embedding")
                    ) if selected else 0.0
                else:
                    max_sim = 0.0

                mmr_score = self.mmr_lambda * relevance - (1 - self.mmr_lambda) * max_sim
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return [{**c, "score_type": "mmr"} for c in selected]


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

hybrid_retriever = HybridRetriever()
mmr_retriever = MMRRetriever(hybrid=hybrid_retriever)
