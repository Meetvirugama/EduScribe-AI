from __future__ import annotations

import math
import re
from typing import Any

from .errors import (
    TranscriptValidationError,
)
from .models import TranscriptSegment


class Canonicalizer:

    @classmethod
    def canonicalize_youtube_captions(
        cls,
        raw_segments: list[dict[str, Any]],
        language: str,
        *,
        source: str = "youtube_captions",
    ) -> list[TranscriptSegment]:

        canonical = []

        for raw in raw_segments:

            start = cls._finite_non_negative(
                raw.get("start"),
                "start",
            )

            duration = cls._finite_non_negative(
                raw.get("duration"),
                "duration",
            )

            end = start + duration

            text = cls._normalize_text(
                raw.get("text")
            )

            # Empty cues are ignored.
            if not text:
                continue

            if end <= start:
                raise TranscriptValidationError(
                    "Caption segment has invalid duration."
                )

            canonical.append(
                TranscriptSegment(
                    index=len(canonical) + 1,
                    start=start,
                    end=end,
                    text=text,
                    language=language,
                    speaker=None,

                    # YouTube caption does NOT give us a
                    # reliable 0..1 confidence.
                    confidence=None,

                    avg_logprob=None,
                    source=source,
                )
            )

        return cls.reindex(
            canonical
        )

    @classmethod
    def canonicalize_whisper_stt(
        cls,
        whisper_segments: list[dict[str, Any]],
        language: str,
    ) -> list[TranscriptSegment]:

        canonical = []

        for raw in whisper_segments:

            start = cls._finite_non_negative(
                raw.get("start"),
                "start",
            )

            end = cls._finite_non_negative(
                raw.get("end"),
                "end",
            )

            if end <= start:
                continue

            text = cls._normalize_text(
                raw.get("text")
            )

            if not text:
                continue

            avg_logprob = (
                cls._optional_float(
                    raw.get(
                        "avg_logprob"
                    )
                )
            )

            canonical.append(
                TranscriptSegment(
                    index=len(canonical) + 1,
                    start=start,
                    end=end,
                    text=text,
                    language=language,
                    speaker=raw.get(
                        "speaker"
                    ),

                    # IMPORTANT:
                    # avg_logprob is NOT a normalized
                    # 0..1 confidence value.
                    confidence=None,

                    avg_logprob=avg_logprob,
                    source="whisper_stt",
                )
            )

        return cls.reindex(
            canonical
        )

    @classmethod
    def reindex(
        cls,
        segments: list[TranscriptSegment],
    ) -> list[TranscriptSegment]:

        result = []

        for index, segment in enumerate(
            segments,
            start=1,
        ):
            # Because TranscriptSegment is a frozen dataclass, we must use object.__setattr__ 
            # or recreate the object to update the index. Recreating is safer.
            new_segment = TranscriptSegment(
                index=index,
                start=segment.start,
                end=segment.end,
                text=segment.text,
                language=segment.language,
                speaker=segment.speaker,
                confidence=segment.confidence,
                avg_logprob=segment.avg_logprob,
                source=segment.source
            )
            result.append(new_segment)

        return result

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        text = str(value)

        text = (
            text
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _finite_non_negative(
        value: Any,
        field: str,
    ) -> float:

        try:
            result = float(value)

        except (
            TypeError,
            ValueError,
        ):

            raise TranscriptValidationError(
                f"Invalid {field} timestamp."
            )

        if (
            not math.isfinite(result)
            or result < 0
        ):

            raise TranscriptValidationError(
                f"Invalid {field} timestamp."
            )

        return result

    @staticmethod
    def _optional_float(
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        try:
            result = float(value)

        except (
            TypeError,
            ValueError,
        ):

            return None

        if not math.isfinite(result):
            return None

        return result
