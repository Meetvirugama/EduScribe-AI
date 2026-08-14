from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TranscriptSourceType(str, Enum):
    MANUAL_CAPTION = "manual_caption"
    GENERATED_CAPTION = "generated_caption"
    TRANSLATED_CAPTION = "translated_caption"
    STT = "stt"


class DiscoveryStatus(str, Enum):
    SUCCESS = "SUCCESS"
    NO_SOURCE = "NO_SOURCE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class TranscriptSegment:
    index: int
    start: float
    end: float
    text: str
    language: str | None = None
    speaker: str | None = None
    confidence: float | None = None
    avg_logprob: float | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "language": self.language,
            "speaker": self.speaker,
            "confidence": self.confidence,
            "avg_logprob": self.avg_logprob,
            "source": self.source,
        }


@dataclass
class CaptionAcquisitionResult:
    status: DiscoveryStatus
    video_id: str
    requested_language: str

    actual_language: str | None = None
    actual_language_code: str | None = None

    source_type: TranscriptSourceType | None = None

    is_generated: bool | None = None
    is_translatable: bool | None = None

    translated: bool = False

    segments: list[dict[str, Any]] = field(default_factory=list)

    reason: str | None = None

    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "video_id": self.video_id,
            "requested_language": self.requested_language,
            "actual_language": self.actual_language,
            "actual_language_code": self.actual_language_code,
            "source_type": (
                self.source_type.value
                if self.source_type
                else None
            ),
            "is_generated": self.is_generated,
            "is_translatable": self.is_translatable,
            "translated": self.translated,
            "segments": self.segments,
            "reason": self.reason,
            "errors": self.errors,
        }


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "warning"
    segment_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "segment_index": self.segment_index,
        }


@dataclass
class ValidationResult:
    valid: bool
    segments: list[dict[str, Any]]
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "segments": self.segments,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
        }
