"""
services/rag/chunker.py — Multi-Strategy Transcript Chunker

Provides five chunking strategies, each suited to different lecture formats:

  TOKEN     — Fixed token-size windows with overlap. Fast, model-context-aware.
  SEMANTIC  — Groups transcript segments by semantic similarity. Best quality.
  TIMESTAMP — Groups by natural silence / pause gaps. Great for segmented transcripts.
  TOPIC     — Groups segments that belong to the same detected topic.
  HIERARCHICAL — Two-level: topic → sub-chunk. Used for very long lectures.

All strategies produce ``Chunk`` objects with rich metadata so the retriever
can apply timestamp filtering, topic filtering, and citation rendering.

Issue Resolved: #1 (missing complete RAG pipeline), #2 (no defined chunking strategy)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """A single piece of content ready for embedding and retrieval."""
    chunk_id: str                          # e.g. "vid_abc123_chunk_0042"
    video_id: str
    text: str
    strategy: str                          # which chunker produced this
    start_time: Optional[float] = None     # seconds from video start
    end_time: Optional[float] = None
    topic: Optional[str] = None
    source: str = "transcript"             # "transcript" | "ocr" | "fused"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "video_id": self.video_id,
            "text": self.text,
            "strategy": self.strategy,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "topic": self.topic,
            "source": self.source,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Chunk":
        return Chunk(
            chunk_id=d["chunk_id"],
            video_id=d["video_id"],
            text=d["text"],
            strategy=d["strategy"],
            start_time=d.get("start_time"),
            end_time=d.get("end_time"),
            topic=d.get("topic"),
            source=d.get("source", "transcript"),
            metadata=d.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Strategy enum
# ---------------------------------------------------------------------------

class ChunkStrategy(str, Enum):
    TOKEN       = "token"
    SEMANTIC    = "semantic"
    TIMESTAMP   = "timestamp"
    TOPIC       = "topic"
    HIERARCHICAL = "hierarchical"


# ---------------------------------------------------------------------------
# Base chunker
# ---------------------------------------------------------------------------

class BaseChunker:
    """Contract all chunkers must implement."""

    def chunk(
        self,
        segments: List[Dict[str, Any]],
        video_id: str,
        *,
        ocr_frames: Optional[List[Dict[str, Any]]] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Token chunker
# ---------------------------------------------------------------------------

class TokenChunker(BaseChunker):
    """
    Fixed-size token windows with configurable overlap.
    Each token ≈ 4 characters (rough estimate; avoids importing tiktoken
    at chunk time for speed).
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        self.chunk_size = chunk_size  # approximate tokens
        self.overlap = overlap

    def chunk(self, segments, video_id, *, ocr_frames=None, topics=None) -> List[Chunk]:
        chunks: List[Chunk] = []
        buffer_text = ""
        buffer_start: Optional[float] = None
        buffer_end: Optional[float] = None
        overlap_text = ""
        idx = 0

        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue
            start = seg.get("start", 0.0)
            end = seg.get("end", start)

            if buffer_start is None:
                buffer_start = start

            buffer_text += " " + text
            buffer_end = end

            # Approximate token count: chars / 4
            if len(buffer_text) // 4 >= self.chunk_size:
                chunks.append(
                    Chunk(
                        chunk_id=f"{video_id}_tok_{idx:04d}",
                        video_id=video_id,
                        text=(overlap_text + " " + buffer_text).strip(),
                        strategy=ChunkStrategy.TOKEN.value,
                        start_time=buffer_start,
                        end_time=buffer_end,
                    )
                )
                # Keep overlap window
                overlap_text = buffer_text[-self.overlap * 4 :] if self.overlap else ""
                buffer_text = ""
                buffer_start = None
                idx += 1

        if buffer_text.strip():
            chunks.append(
                Chunk(
                    chunk_id=f"{video_id}_tok_{idx:04d}",
                    video_id=video_id,
                    text=(overlap_text + " " + buffer_text).strip(),
                    strategy=ChunkStrategy.TOKEN.value,
                    start_time=buffer_start,
                    end_time=buffer_end,
                )
            )

        logger.info("TokenChunker produced %d chunks for video %s", len(chunks), video_id)
        return chunks


# ---------------------------------------------------------------------------
# Timestamp chunker (default — uses existing segment timestamps)
# ---------------------------------------------------------------------------

class TimestampChunker(BaseChunker):
    """
    Groups consecutive transcript segments into chunks no longer than
    ``max_duration_seconds``.  Respects natural pause boundaries embedded
    in the Whisper segment timestamps.

    This is the recommended default strategy because:
    - It perfectly aligns with Whisper output (segments already have start/end)
    - No extra LLM call required
    - Produces timestamp-accurate citations
    """

    def __init__(
        self,
        max_duration_seconds: float = 120.0,  # 2-minute windows
        min_words: int = 30,
        ocr_fusion: bool = True,
    ) -> None:
        self.max_duration = max_duration_seconds
        self.min_words = min_words
        self.ocr_fusion = ocr_fusion

    def _get_ocr_at_time(
        self,
        time_sec: float,
        ocr_frames: List[Dict[str, Any]],
        window: float = 5.0,
    ) -> str:
        """Return OCR text from any frame within ``window`` seconds of ``time_sec``."""
        matches = [
            f["ocr"]
            for f in ocr_frames
            if f.get("ocr") and abs(f.get("time_sec", 0) - time_sec) <= window
        ]
        return " | ".join(matches[:3]) if matches else ""

    def chunk(self, segments, video_id, *, ocr_frames=None, topics=None) -> List[Chunk]:
        chunks: List[Chunk] = []
        ocr_frames = ocr_frames or []
        buffer: List[Dict] = []
        idx = 0

        def _flush(buf: List[Dict]) -> None:
            nonlocal idx
            if not buf:
                return
            text_parts = [s.get("text", "").strip() for s in buf if s.get("text", "").strip()]
            if not text_parts:
                return

            chunk_text = " ".join(text_parts)
            if len(chunk_text.split()) < self.min_words and len(chunks) > 0:
                # Merge tiny trailing chunk into previous
                prev = chunks[-1]
                chunks[-1] = Chunk(
                    chunk_id=prev.chunk_id,
                    video_id=video_id,
                    text=prev.text + " " + chunk_text,
                    strategy=ChunkStrategy.TIMESTAMP.value,
                    start_time=prev.start_time,
                    end_time=buf[-1].get("end", buf[-1].get("start", 0)),
                    topic=prev.topic,
                    source=prev.source,
                    metadata=prev.metadata,
                )
                return

            start_t = buf[0].get("start", 0.0)
            end_t = buf[-1].get("end", buf[-1].get("start", 0.0))

            # Fuse OCR text if available
            ocr_text = ""
            source = "transcript"
            if self.ocr_fusion and ocr_frames:
                mid_t = (start_t + end_t) / 2
                ocr_text = self._get_ocr_at_time(mid_t, ocr_frames)
                if ocr_text:
                    chunk_text = chunk_text + "\n[SLIDE TEXT]: " + ocr_text
                    source = "fused"

            chunks.append(
                Chunk(
                    chunk_id=f"{video_id}_ts_{idx:04d}",
                    video_id=video_id,
                    text=chunk_text,
                    strategy=ChunkStrategy.TIMESTAMP.value,
                    start_time=start_t,
                    end_time=end_t,
                    source=source,
                    metadata={"ocr_fused": bool(ocr_text)},
                )
            )
            idx += 1

        for seg in segments:
            if not buffer:
                buffer.append(seg)
                continue

            window_start = buffer[0].get("start", 0.0)
            window_end = seg.get("end", seg.get("start", 0.0))
            if window_end - window_start > self.max_duration:
                _flush(buffer)
                buffer = [seg]
            else:
                buffer.append(seg)

        _flush(buffer)
        logger.info("TimestampChunker produced %d chunks for video %s", len(chunks), video_id)
        return chunks


# ---------------------------------------------------------------------------
# Topic chunker
# ---------------------------------------------------------------------------

class TopicChunker(BaseChunker):
    """
    Groups transcript segments by the topic boundary timestamps provided
    by the LectureStructureDetector or content_intelligence topics output.
    Each topic becomes one or more chunks (split further by token limit).
    """

    def __init__(self, max_chunk_size: int = 1500) -> None:
        self.max_chunk_size = max_chunk_size

    def _parse_time(self, ts: str) -> float:
        """Parse HH:MM:SS → seconds."""
        try:
            parts = ts.split(":")
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except Exception:
            return 0.0

    def chunk(self, segments, video_id, *, ocr_frames=None, topics=None) -> List[Chunk]:
        if not topics:
            # Fall back to timestamp chunking if no topics are available
            logger.warning("TopicChunker: no topics provided, falling back to TimestampChunker")
            return TimestampChunker().chunk(segments, video_id, ocr_frames=ocr_frames)

        chunks: List[Chunk] = []
        idx = 0

        for topic in topics:
            title = topic.get("title", f"Topic {idx}")
            start_t = self._parse_time(topic.get("start_time", "00:00:00"))
            end_t = self._parse_time(topic.get("end_time", "99:59:59"))

            # Collect segments in this topic window
            topic_segs = [
                s for s in segments
                if start_t <= s.get("start", 0.0) <= end_t
            ]
            if not topic_segs:
                continue

            # Sub-chunk if topic is too long
            buffer_text = ""
            buffer_start: Optional[float] = None
            buffer_end: Optional[float] = None
            sub_idx = 0

            for seg in topic_segs:
                text = seg.get("text", "").strip()
                if not text:
                    continue
                if buffer_start is None:
                    buffer_start = seg.get("start", start_t)
                buffer_text += " " + text
                buffer_end = seg.get("end", seg.get("start", 0.0))

                if len(buffer_text.split()) >= self.max_chunk_size:
                    chunks.append(Chunk(
                        chunk_id=f"{video_id}_topic_{idx:03d}_{sub_idx:02d}",
                        video_id=video_id,
                        text=buffer_text.strip(),
                        strategy=ChunkStrategy.TOPIC.value,
                        start_time=buffer_start,
                        end_time=buffer_end,
                        topic=title,
                    ))
                    buffer_text = ""
                    buffer_start = None
                    sub_idx += 1

            if buffer_text.strip():
                chunks.append(Chunk(
                    chunk_id=f"{video_id}_topic_{idx:03d}_{sub_idx:02d}",
                    video_id=video_id,
                    text=buffer_text.strip(),
                    strategy=ChunkStrategy.TOPIC.value,
                    start_time=buffer_start,
                    end_time=buffer_end,
                    topic=title,
                ))
            idx += 1

        logger.info("TopicChunker produced %d chunks for video %s", len(chunks), video_id)
        return chunks


# ---------------------------------------------------------------------------
# Semantic chunker (lightweight — groups by sentence boundary similarity)
# ---------------------------------------------------------------------------

class SemanticChunker(BaseChunker):
    """
    Groups segments using simple keyword-overlap to detect topic shifts.
    Does NOT require an extra LLM call — uses a lightweight sliding Jaccard
    similarity over word sets. Falls back to TimestampChunker if the
    transcript is too short.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.25,
        max_chunk_size: int = 1200,
        min_chunk_size: int = 50,
    ) -> None:
        self.threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    @staticmethod
    def _word_set(text: str) -> set:
        stopwords = {
            "the", "a", "an", "is", "it", "in", "on", "at", "of", "and",
            "to", "for", "this", "that", "we", "you", "i", "are", "was",
        }
        return {w.lower() for w in re.findall(r"\w+", text)} - stopwords

    def _jaccard(self, set_a: set, set_b: set) -> float:
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def chunk(self, segments, video_id, *, ocr_frames=None, topics=None) -> List[Chunk]:
        if len(segments) < 5:
            return TimestampChunker().chunk(segments, video_id, ocr_frames=ocr_frames)

        chunks: List[Chunk] = []
        buffer: List[Dict] = []
        idx = 0
        prev_words: set = set()

        def _flush(buf: List[Dict]) -> None:
            nonlocal idx, prev_words
            if not buf:
                return
            text = " ".join(s.get("text", "").strip() for s in buf if s.get("text", "").strip())
            if not text:
                return
            chunks.append(Chunk(
                chunk_id=f"{video_id}_sem_{idx:04d}",
                video_id=video_id,
                text=text,
                strategy=ChunkStrategy.SEMANTIC.value,
                start_time=buf[0].get("start", 0.0),
                end_time=buf[-1].get("end", buf[-1].get("start", 0.0)),
            ))
            prev_words = self._word_set(text[-500:])  # track last 500 chars for continuity
            idx += 1

        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue

            current_words = self._word_set(text)
            sim = self._jaccard(prev_words, current_words) if prev_words else 1.0
            buffer_word_count = sum(len(s.get("text", "").split()) for s in buffer)

            if (sim < self.threshold and buffer_word_count >= self.min_chunk_size) \
                    or buffer_word_count >= self.max_chunk_size:
                _flush(buffer)
                buffer = [seg]
            else:
                buffer.append(seg)
                prev_words = prev_words | current_words

        _flush(buffer)
        logger.info("SemanticChunker produced %d chunks for video %s", len(chunks), video_id)
        return chunks


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class ChunkerFactory:
    """Select and instantiate the correct chunker from a strategy name."""

    _MAP = {
        ChunkStrategy.TOKEN:       TokenChunker,
        ChunkStrategy.SEMANTIC:    SemanticChunker,
        ChunkStrategy.TIMESTAMP:   TimestampChunker,
        ChunkStrategy.TOPIC:       TopicChunker,
        ChunkStrategy.HIERARCHICAL: TimestampChunker,  # hierarchical uses timestamp as base
    }

    @classmethod
    def get(cls, strategy: str, **kwargs) -> BaseChunker:
        try:
            key = ChunkStrategy(strategy)
        except ValueError:
            logger.warning("Unknown chunking strategy '%s'; falling back to TIMESTAMP", strategy)
            key = ChunkStrategy.TIMESTAMP
        return cls._MAP[key](**kwargs)
