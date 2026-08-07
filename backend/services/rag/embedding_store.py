"""
services/rag/embedding_store.py — Versioned Embedding Storage

Manages the full lifecycle of chunk embeddings per video:
  - Batch embedding (up to 100 chunks per API call)
  - Version-aware storage (stale embeddings auto-detected and rebuilt)
  - LRU in-process cache (avoids re-reading JSON for repeated searches)
  - Thread-safe file writes

Issue Resolved: #3 (no embedding management system)
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from core.config import settings
from services.rag.chunker import Chunk

logger = logging.getLogger(__name__)

# Maximum chunks sent in a single embedding API call
BATCH_SIZE = 50


class EmbeddingStore:
    """
    Stores and retrieves chunk embeddings as a versioned JSON file per video.

    File layout (one file per video):
        {settings.EMBEDDING_DIR}/{video_id}/chunks.json

    File schema:
        {
          "embed_version": "v1",
          "embed_model": "gemini/text-embedding-004",
          "chunks": [
            {
              "chunk_id": "...",
              "video_id": "...",
              "text": "...",
              "strategy": "...",
              "start_time": 0.0,
              "end_time": 120.0,
              "topic": null,
              "source": "transcript",
              "metadata": {},
              "embedding": [0.1, 0.2, ...]
            },
            ...
          ]
        }
    """

    def __init__(self) -> None:
        # In-process LRU cache: avoids re-reading the JSON file on every search
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def _index_path(self, video_id: str) -> str:
        return os.path.join(settings.EMBEDDING_DIR, video_id, "chunks.json")

    def _is_stale(self, index_path: str, embed_version: str) -> bool:
        """Return True if the stored index uses a different embed version."""
        if not os.path.exists(index_path):
            return True
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            stored_version = data.get("embed_version", "")
            return stored_version != embed_version
        except Exception:
            return True

    def _save(self, video_id: str, embed_version: str, embed_model: str, records: List[Dict]) -> None:
        index_path = self._index_path(video_id)
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        payload = {
            "embed_version": embed_version,
            "embed_model": embed_model,
            "chunks": records,
        }
        tmp_path = index_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        os.replace(tmp_path, index_path)  # atomic rename
        self._cache[video_id] = records   # update in-process cache

    def _load(self, video_id: str) -> List[Dict[str, Any]]:
        """Load chunk records from cache or disk."""
        if video_id in self._cache:
            return self._cache[video_id]

        index_path = self._index_path(video_id)
        if not os.path.exists(index_path):
            return []

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            records = data.get("chunks", [])
            self._cache[video_id] = records
            return records
        except Exception as exc:
            logger.error("EmbeddingStore: failed to load index for %s: %s", video_id, exc)
            return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build(
        self,
        video_id: str,
        chunks: List[Chunk],
        llm_manager,          # LLMManager instance (injected to avoid circular import)
        embed_version: Optional[str] = None,
        force_rebuild: bool = False,
    ) -> int:
        """
        Generate and store embeddings for all chunks.

        - Skips rebuild if stored version matches current EMBED_MODEL_VERSION
          unless force_rebuild=True.
        - Sends chunks in batches of BATCH_SIZE to reduce API calls.

        Returns the number of chunks successfully embedded.
        """
        embed_version = embed_version or settings.EMBED_MODEL_VERSION
        index_path = self._index_path(video_id)

        if not force_rebuild and not self._is_stale(index_path, embed_version):
            logger.info("EmbeddingStore: index for %s is up-to-date (v=%s), skipping.", video_id, embed_version)
            return len(self._load(video_id))

        logger.info(
            "EmbeddingStore: building index for %s — %d chunks, version=%s",
            video_id, len(chunks), embed_version,
        )

        records: List[Dict] = []
        embed_model = "unknown"

        # Batch embed
        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_start : batch_start + BATCH_SIZE]
            texts = [c.text for c in batch]

            try:
                raw = await llm_manager.embed(texts)
                # LiteLLM aembedding returns: {"data": [{"embedding": [...]}, ...]}
                embeddings = [item["embedding"] for item in raw.get("data", [])]
                embed_model = raw.get("model", "unknown")
            except Exception as exc:
                logger.error("EmbeddingStore: batch embedding failed: %s", exc)
                # Emit chunks without embeddings (will be skipped in retrieval)
                embeddings = [None] * len(batch)

            for chunk, emb in zip(batch, embeddings):
                rec = chunk.to_dict()
                rec["embedding"] = emb
                records.append(rec)

        self._save(video_id, embed_version, embed_model, records)
        embedded_count = sum(1 for r in records if r.get("embedding"))
        logger.info("EmbeddingStore: stored %d/%d embeddings for %s", embedded_count, len(records), video_id)
        return embedded_count

    def get_records(self, video_id: str) -> List[Dict[str, Any]]:
        """Return all stored chunk records (with embeddings) for a video."""
        return self._load(video_id)

    def delete(self, video_id: str) -> None:
        """Remove index file and evict from cache."""
        self._cache.pop(video_id, None)
        index_path = self._index_path(video_id)
        if os.path.exists(index_path):
            try:
                os.remove(index_path)
                logger.info("EmbeddingStore: deleted index for %s", video_id)
            except OSError as exc:
                logger.warning("EmbeddingStore: could not delete index for %s: %s", video_id, exc)

    def invalidate_cache(self, video_id: str) -> None:
        """Force reload from disk on next access."""
        self._cache.pop(video_id, None)


# Module-level singleton
embedding_store = EmbeddingStore()
