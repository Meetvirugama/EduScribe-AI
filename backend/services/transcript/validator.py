from __future__ import annotations

import math
from typing import Any, Union

from .models import (
    ValidationIssue,
    ValidationResult,
    TranscriptSegment,
)


class TranscriptValidator:

    @classmethod
    def validate(
        cls,
        segments: list[Union[dict[str, Any], TranscriptSegment]],
        *,
        media_duration: float | None = None,
        allow_empty: bool = False,
    ) -> ValidationResult:

        issues = []
        valid_segments = []

        if not segments:

            issues.append(
                ValidationIssue(
                    code="EMPTY_TRANSCRIPT",
                    message=(
                        "Transcript contains no usable segments."
                    ),
                    severity="error",
                )
            )

            return ValidationResult(
                valid=allow_empty,
                segments=[],
                issues=issues,
            )

        previous_start = -1.0

        for position, segment in enumerate(
            segments,
            start=1,
        ):
            if isinstance(segment, dict):
                index = segment.get("index", position)
                start_raw = segment.get("start")
                end_raw = segment.get("end")
                text_raw = segment.get("text")
                language = segment.get("language")
                speaker = segment.get("speaker")
                confidence = segment.get("confidence")
                avg_logprob = segment.get("avg_logprob")
                source = segment.get("source")
            else:
                index = getattr(segment, "index", position)
                start_raw = segment.start
                end_raw = segment.end
                text_raw = segment.text
                language = segment.language
                speaker = segment.speaker
                confidence = segment.confidence
                avg_logprob = segment.avg_logprob
                source = segment.source

            start = cls._number(start_raw)
            end = cls._number(end_raw)

            text = str(
                text_raw or ""
            ).strip()

            if start is None:

                issues.append(
                    ValidationIssue(
                        "INVALID_START",
                        "Start timestamp is invalid.",
                        "error",
                        index,
                    )
                )

                continue

            if end is None:

                issues.append(
                    ValidationIssue(
                        "INVALID_END",
                        "End timestamp is invalid.",
                        "error",
                        index,
                    )
                )

                continue

            if start < 0:

                issues.append(
                    ValidationIssue(
                        "NEGATIVE_START",
                        "Start timestamp is negative.",
                        "error",
                        index,
                    )
                )

                continue

            if end <= start:

                issues.append(
                    ValidationIssue(
                        "INVALID_INTERVAL",
                        "End must be greater than start.",
                        "error",
                        index,
                    )
                )

                continue

            if not text:

                issues.append(
                    ValidationIssue(
                        "EMPTY_SEGMENT",
                        "Segment text is empty.",
                        "warning",
                        index,
                    )
                )

                continue

            if start < previous_start:

                issues.append(
                    ValidationIssue(
                        "OUT_OF_ORDER",
                        "Segment starts before previous segment.",
                        "warning",
                        index,
                    )
                )

            if media_duration is not None:

                if (
                    math.isfinite(
                        media_duration
                    )
                    and media_duration >= 0
                ):

                    if start > media_duration:

                        issues.append(
                            ValidationIssue(
                                "START_AFTER_MEDIA",
                                "Segment starts after media duration.",
                                "error",
                                index,
                            )
                        )

                        continue

                    if (
                        end
                        > media_duration + 2.0
                    ):

                        issues.append(
                            ValidationIssue(
                                "END_AFTER_MEDIA",
                                "Segment extends beyond media duration.",
                                "warning",
                                index,
                            )
                        )

            # Store internally as TranscriptSegment for next checks
            valid_segments.append(
                TranscriptSegment(
                    index=index,
                    start=start,
                    end=end,
                    text=text,
                    language=language,
                    speaker=speaker,
                    confidence=confidence,
                    avg_logprob=avg_logprob,
                    source=source
                )
            )

            previous_start = start

        # Exact duplicates.
        for previous, current in zip(
            valid_segments,
            valid_segments[1:],
        ):

            if (
                previous.text.casefold()
                == current.text.casefold()
                and abs(
                    previous.start
                    - current.start
                )
                < 0.001
                and abs(
                    previous.end
                    - current.end
                )
                < 0.001
            ):

                issues.append(
                    ValidationIssue(
                        "EXACT_DUPLICATE",
                        "Adjacent segments are exact duplicates.",
                        "warning",
                        current.index,
                    )
                )

            if (
                current.start
                < previous.end
            ):

                issues.append(
                    ValidationIssue(
                        "OVERLAP",
                        "Adjacent segments overlap.",
                        "warning",
                        current.index,
                    )
                )

        valid = not any(
            issue.severity == "error"
            for issue in issues
        )

        return ValidationResult(
            valid=valid,
            segments=cls._reindex(
                valid_segments
            ),
            issues=issues,
        )

    @classmethod
    def coverage_ratio(
        cls,
        segments: list[Union[dict[str, Any], TranscriptSegment]],
        media_duration: float | None,
    ) -> float | None:

        if (
            media_duration is None
            or media_duration <= 0
        ):
            return None

        intervals = []

        for segment in segments:
            
            if isinstance(segment, dict):
                start = cls._number(segment.get("start"))
                end = cls._number(segment.get("end"))
            else:
                start = cls._number(segment.start)
                end = cls._number(segment.end)

            if (
                start is None
                or end is None
                or end <= start
            ):
                continue

            intervals.append(
                (
                    start,
                    end,
                )
            )

        if not intervals:
            return 0.0

        intervals.sort()

        merged = []

        for start, end in intervals:

            start = max(
                0.0,
                start,
            )

            end = min(
                float(media_duration),
                end,
            )

            if end <= start:
                continue

            if (
                not merged
                or start > merged[-1][1]
            ):

                merged.append(
                    [
                        start,
                        end,
                    ]
                )

            else:

                merged[-1][1] = max(
                    merged[-1][1],
                    end,
                )

        covered = sum(
            end - start
            for start, end in merged
        )

        return min(
            1.0,
            covered / float(
                media_duration
            ),
        )

    @staticmethod
    def _number(
        value: Any,
    ) -> float | None:

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

    @staticmethod
    def _reindex(
        segments: list[TranscriptSegment],
    ) -> list[TranscriptSegment]:

        result = []

        for index, segment in enumerate(
            segments,
            start=1,
        ):
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
