from __future__ import annotations

from collections import Counter
from typing import Any, Union

from .validator import (
    TranscriptValidator,
)
from .models import TranscriptSegment, ValidationIssue


class QualityEngine:
    """
    Heuristic transcript quality assessment.

    IMPORTANT:
    This score is NOT transcription accuracy.
    """

    @classmethod
    def assess(
        cls,
        segments: list[Union[dict[str, Any], TranscriptSegment]],
        *,
        media_duration: float | None = None,
        requested_language: str | None = None,
        actual_language: str | None = None,
        source_type: str | None = None,
        validation_issues: list[Union[dict[str, Any], ValidationIssue]] | None = None,
    ) -> dict[str, Any]:

        validation_issues = (
            validation_issues or []
        )

        warnings = []

        if not segments:

            return {
                "score": 0.0,
                "level": "LOW",
                "is_accuracy_percentage": False,
                "warnings": [
                    {
                        "code": "EMPTY_TRANSCRIPT",
                        "message": (
                            "Transcript contains no segments."
                        ),
                    }
                ],
            }

        score = 1.0

        error_count = sum(
            1
            for issue in validation_issues
            if (issue.severity if hasattr(issue, "severity") else issue.get("severity"))
            == "error"
        )

        warning_count = sum(
            1
            for issue in validation_issues
            if (issue.severity if hasattr(issue, "severity") else issue.get("severity"))
            == "warning"
        )

        score -= min(
            0.45,
            error_count * 0.15,
        )

        score -= min(
            0.20,
            warning_count * 0.02,
        )

        coverage = (
            TranscriptValidator.coverage_ratio(
                segments,
                media_duration,
            )
        )

        if coverage is not None:

            if coverage < 0.01:

                score -= 0.45

                warnings.append(
                    {
                        "code": "VERY_LOW_COVERAGE",
                        "message": (
                            f"Coverage: {coverage:.1%}"
                        ),
                    }
                )

            elif coverage < 0.20:

                score -= 0.25

                warnings.append(
                    {
                        "code": "LOW_COVERAGE",
                        "message": (
                            f"Coverage: {coverage:.1%}"
                        ),
                    }
                )

            elif coverage < 0.80:

                score -= 0.08

                warnings.append(
                    {
                        "code": "PARTIAL_COVERAGE",
                        "message": (
                            f"Coverage: {coverage:.1%}"
                        ),
                    }
                )

        if source_type == (
            "generated_caption"
        ):

            score -= 0.03

            warnings.append(
                {
                    "code": "AUTO_GENERATED_CAPTION",
                    "message": (
                        "Automatically generated captions were used."
                    ),
                }
            )

        elif source_type == (
            "translated_caption"
        ):

            score -= 0.05

            warnings.append(
                {
                    "code": "TRANSLATED_CAPTION",
                    "message": (
                        "Source-platform translation was used."
                    ),
                }
            )

        elif source_type == "stt":

            score -= 0.03

            warnings.append(
                {
                    "code": "STT_SOURCE",
                    "message": (
                        "Transcript was generated using speech recognition."
                    ),
                }
            )

        if (
            requested_language
            and actual_language
            and cls._normalize_language(
                requested_language
            )
            != cls._normalize_language(
                actual_language
            )
        ):

            score -= 0.20

            warnings.append(
                {
                    "code": "LANGUAGE_MISMATCH",
                    "message": (
                        f"Requested={requested_language}, "
                        f"actual={actual_language}"
                    ),
                }
            )

        duplicate_ratio = (
            cls._duplicate_ratio(
                segments
            )
        )

        if duplicate_ratio > 0.20:

            score -= 0.15

            warnings.append(
                {
                    "code": "HIGH_DUPLICATE_RATIO",
                    "message": (
                        f"Duplicate ratio: {duplicate_ratio:.1%}"
                    ),
                }
            )

        elif duplicate_ratio > 0.05:

            score -= 0.05

            warnings.append(
                {
                    "code": "DUPLICATE_SEGMENTS",
                    "message": (
                        f"Duplicate ratio: {duplicate_ratio:.1%}"
                    ),
                }
            )

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        if score >= 0.90:
            level = "HIGH"

        elif score >= 0.70:
            level = "MEDIUM"

        else:
            level = "LOW"

        return {
            "score": round(
                score,
                4,
            ),
            "level": level,
            "is_accuracy_percentage": False,
            "coverage_ratio": coverage,
            "duplicate_ratio": duplicate_ratio,
            "warnings": warnings,
            "validation_issues": validation_issues,
        }

    @staticmethod
    def _duplicate_ratio(
        segments: list[Union[dict[str, Any], TranscriptSegment]],
    ) -> float:

        if not segments:
            return 0.0

        texts = [
            str(
                segment.text if hasattr(segment, "text") else segment.get("text")
                or ""
            )
            .strip()
            .casefold()
            for segment in segments
        ]

        counts = Counter(
            texts
        )

        duplicates = sum(
            count - 1
            for count in counts.values()
            if count > 1
        )

        return duplicates / len(
            texts
        )

    @staticmethod
    def _normalize_language(
        value: str,
    ) -> str:

        return (
            str(value or "")
            .strip()
            .lower()
            .replace("_", "-")
        )
