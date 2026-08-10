"""
services/rag/context_optimizer.py — Token-Aware Context Builder

Prevents context overflow by:
  1. Counting tokens in the assembled prompt before sending
  2. Removing near-duplicate retrieved chunks
  3. Priority-ranked truncation when the total exceeds max_tokens
  4. Producing a final safe context string for prompt construction

Issue Resolved: #7 (no context window optimization)
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Rough characters-per-token estimate (avoids tiktoken import at call-time)
_CHARS_PER_TOKEN = 4

# Tokens reserved for the prompt template itself (system message, instructions, etc.)
_PROMPT_OVERHEAD_TOKENS = 800


def _rough_tokens(text: str) -> int:
    """Estimate token count without importing tiktoken."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _try_token_counter(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Use litellm.token_counter if available, fall back to rough estimate."""
    try:
        import litellm  # type: ignore
        return litellm.token_counter(model=model, messages=[{"role": "user", "content": text}])
    except Exception:
        return _rough_tokens(text)


class DuplicateFilter:
    """
    Remove near-duplicate chunks from a retrieved set using Jaccard similarity
    on word sets (same approach as SemanticChunker — zero extra dependencies).
    """

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    @staticmethod
    def _word_set(text: str) -> set:
        return {w.lower() for w in re.findall(r"\w+", text) if len(w) > 2}

    def _jaccard(self, a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def deduplicate(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique: List[Dict] = []
        unique_word_sets: List[set] = []

        for chunk in chunks:
            ws = self._word_set(chunk.get("text", ""))
            is_dup = any(
                self._jaccard(ws, existing) >= self.threshold
                for existing in unique_word_sets
            )
            if not is_dup:
                unique.append(chunk)
                unique_word_sets.append(ws)

        removed = len(chunks) - len(unique)
        if removed:
            logger.debug("DuplicateFilter: removed %d near-duplicate chunks", removed)
        return unique


class ContextCompressor:
    """
    Truncates context to fit within max_tokens by removing lower-scored chunks
    from the bottom of the ranked list.
    """

    def compress(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: int,
        overhead_tokens: int = _PROMPT_OVERHEAD_TOKENS,
    ) -> List[Dict[str, Any]]:
        budget = max_tokens - overhead_tokens
        selected: List[Dict] = []
        used = 0

        for chunk in chunks:  # already ordered by relevance
            t = _rough_tokens(chunk.get("text", ""))
            if used + t > budget:
                break
            selected.append(chunk)
            used += t

        dropped = len(chunks) - len(selected)
        if dropped:
            logger.info(
                "ContextCompressor: dropped %d chunks to fit within %d tokens (budget=%d)",
                dropped, max_tokens, budget,
            )
        return selected


class ContextOptimizer:
    """
    Assembles a safe, token-bounded prompt context string from retrieved chunks.

    Usage:
        safe_ctx = context_builder.build(
            chunks=retrieved_chunks,
            max_tokens=model_max_tokens,
        )
        prompt = f"Context:\n{safe_ctx}\n\nQuestion: {query}"
    """

    def __init__(self) -> None:
        self._dedup = DuplicateFilter()
        self._compressor = ContextCompressor()

    def build(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: int = 16_000,
        include_timestamps: bool = True,
    ) -> str:
        """
        Deduplicate, compress, and format chunks into a single context string.
        Chunks with timestamp metadata produce citation-ready labels.
        """
        deduped = self._dedup.deduplicate(chunks)
        compressed = self._compressor.compress(deduped, max_tokens)

        parts: List[str] = []
        for i, chunk in enumerate(compressed, start=1):
            text = chunk.get("text", "").strip()
            if not text:
                continue

            header = f"[Context {i}]"
            if include_timestamps:
                start = chunk.get("start_time")
                end = chunk.get("end_time")
                if start is not None and end is not None:
                    def _fmt(s: float) -> str:
                        m, sec = divmod(int(s), 60)
                        h, m = divmod(m, 60)
                        return f"{h:02d}:{m:02d}:{sec:02d}"
                    header += f" [{_fmt(start)} → {_fmt(end)}]"
            if chunk.get("topic"):
                header += f" Topic: {chunk['topic']}"

            parts.append(f"{header}\n{text}")

        return "\n\n---\n\n".join(parts)

    def build_from_transcript(
        self,
        transcript_segments: List[Dict[str, Any]],
        max_tokens: int = 16_000,
        model: str = "gpt-3.5-turbo",
    ) -> str:
        """
        Build a safe plain-text transcript string for use in non-RAG prompts.
        Truncates long transcripts to fit within max_tokens.
        """
        lines: List[str] = []
        token_budget = max_tokens - _PROMPT_OVERHEAD_TOKENS

        for seg in transcript_segments:
            text = seg.get("text", "").strip()
            if not text:
                continue

            start = seg.get("start", 0)
            m, s = divmod(int(start), 60)
            h, m = divmod(m, 60)
            ts = f"[{h:02d}:{m:02d}:{s:02d}]"
            line = f"{ts} {text}"

            est = _rough_tokens("\n".join(lines) + "\n" + line)
            if est > token_budget:
                logger.info(
                    "ContextBuilder: transcript truncated at %d segments to fit %d tokens",
                    len(lines), max_tokens,
                )
                break
            lines.append(line)

        return "\n".join(lines)


# Module-level singletons
context_optimizer = ContextOptimizer()
