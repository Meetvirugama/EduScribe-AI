"""
services/vector_store.py — RAG Pipeline Facade

This module is the public interface for vector indexing and search.
It now delegates to the full production RAG pipeline in services/rag/:

  build_index()  →  Chunk transcript → Embed chunks → Store versioned index
  search()       →  Embed query → Hybrid BM25+Cosine → MMR → Return top-K

The previous implementation (naive paragraph splitting + simple cosine)
is replaced by the full pipeline while keeping the same public API so
that tasks.py and notes.py require no changes.

Issues Resolved: #1 #2 #3 #4 (RAG pipeline overhaul)
"""
import logging
import os
from typing import Any, Dict, List, Optional

from core.config import settings
from services.rag.chunker import ChunkerFactory
from services.rag.embedding_store import embedding_store
from services.rag.retriever import MMRRetriever, HybridRetriever, hybrid_retriever, mmr_retriever

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Production RAG pipeline facade.

    build_index(video_id, transcript_segments, frames_data, topics)
        → Multi-strategy chunking
        → OCR fusion (when frames_data provided)
        → Batch embedding with versioning
        → Persisted vector index

    search(video_id, query, top_k)
        → Embed query
        → Hybrid BM25 + cosine retrieval
        → MMR diversity reranking
        → Return ranked results with citations
    """

    def __init__(self) -> None:
        from services.llm.llm_manager import LLMManager
        self.llm_manager = LLMManager()

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    async def build_index(
        self,
        video_id: str,
        # Legacy positional arg (markdown_content) or new kwargs
        markdown_content: Optional[str] = None,
        *,
        transcript_segments: Optional[List[Dict]] = None,
        frames_data: Optional[List[Dict]] = None,
        topics: Optional[List[Dict]] = None,
        force_rebuild: bool = False,
    ) -> int:
        """
        Build a vector index for a video.

        Accepts both the legacy call signature (markdown_content string) and
        the new preferred call signature (transcript_segments + frames_data).

        Returns the number of chunks successfully embedded.
        """
        # ── Backward-compat: legacy callers pass markdown_content as a string ─
        if markdown_content and not transcript_segments:
            logger.info(
                "VectorStore: legacy call with markdown_content for %s — "
                "splitting into pseudo-segments.", video_id
            )
            transcript_segments = [
                {"start": i * 60.0, "end": (i + 1) * 60.0, "text": para}
                for i, para in enumerate(markdown_content.split("\n\n"))
                if para.strip()
            ]
            frames_data = []

        if not transcript_segments:
            logger.warning("VectorStore: no transcript segments for %s, skipping index build.", video_id)
            return 0

        # ── Select chunking strategy from config ─────────────────────────────
        strategy = settings.CHUNK_STRATEGY
        chunker = ChunkerFactory.get(
            strategy,
            max_duration_seconds=120.0 if strategy == "timestamp" else None,
            chunk_size=settings.CHUNK_SIZE if strategy in ("token", "semantic") else None,
        )

        # Remove None kwargs for chunkers that don't accept them
        chunks = chunker.chunk(
            transcript_segments,
            video_id,
            ocr_frames=frames_data or [],
            topics=topics,
        )

        if not chunks:
            logger.warning("VectorStore: chunker produced 0 chunks for %s", video_id)
            return 0

        logger.info(
            "VectorStore: %d chunks produced via %s strategy for %s",
            len(chunks), strategy, video_id,
        )

        # ── Embed and persist ─────────────────────────────────────────────────
        embedded = await embedding_store.build(
            video_id=video_id,
            chunks=chunks,
            llm_manager=self.llm_manager,
            embed_version=settings.EMBED_MODEL_VERSION,
            force_rebuild=force_rebuild,
        )
        return embedded

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def search(
        self,
        video_id: str,
        query: str,
        top_k: int = 3,
        *,
        use_mmr: bool = True,
        filter_start: Optional[float] = None,
        filter_end: Optional[float] = None,
        filter_topic: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over the video's vector index.

        Returns a list of result dicts, each containing:
          - text: the retrieved chunk text
          - score: relevance score (0–1)
          - score_type: "mmr" | "hybrid"
          - start_time / end_time: citation timestamps
          - topic: topic label (if available)
        """
        # Embed the query
        try:
            raw = await self.llm_manager.embed(query)
            query_embedding = raw["data"][0]["embedding"]
        except Exception as exc:
            logger.error("VectorStore: query embedding failed for %s: %s", video_id, exc)
            return []

        retriever_kwargs = dict(
            video_id=video_id,
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
            filter_start=filter_start,
            filter_end=filter_end,
            filter_topic=filter_topic,
        )

        try:
            if use_mmr:
                results = await mmr_retriever.retrieve(**retriever_kwargs)
            else:
                results = await hybrid_retriever.retrieve(**retriever_kwargs)
        except Exception as exc:
            logger.error("VectorStore: retrieval failed for %s: %s", video_id, exc)
            return []

        # Return clean response (strip raw embedding vectors from output)
        return [
            {
                "text": r.get("text", ""),
                "score": round(r.get("score", 0.0), 4),
                "score_type": r.get("score_type", "hybrid"),
                "start_time": r.get("start_time"),
                "end_time": r.get("end_time"),
                "topic": r.get("topic"),
                "source": r.get("source", "transcript"),
                "chunk_id": r.get("chunk_id"),
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def delete_index(self, video_id: str) -> None:
        """Remove the vector index for a video (called by cleanup job)."""
        embedding_store.delete(video_id)

    def invalidate_cache(self, video_id: str) -> None:
        """Force reload from disk on next access."""
        embedding_store.invalidate_cache(video_id)

    async def rebuild_index(self, video_id: str, transcript_segments: List[Dict], **kwargs) -> int:
        """Force a full rebuild even if the current version is up-to-date."""
        return await self.build_index(
            video_id,
            transcript_segments=transcript_segments,
            force_rebuild=True,
            **kwargs,
        )


# Module-level singleton (same name as before to maintain compatibility)
vector_store = VectorStoreService()
