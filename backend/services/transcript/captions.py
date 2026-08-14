from __future__ import annotations

import asyncio
from typing import Any, Iterable

from youtube_transcript_api import (
    YouTubeTranscriptApi,
)

from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
)

from .models import (
    CaptionAcquisitionResult,
    DiscoveryStatus,
    TranscriptSourceType,
)


class CaptionDiscovery:

    @classmethod
    async def discover_and_acquire(
        cls,
        video_id: str,
        requested_language: str = "en",
        *,
        allow_translation: bool = False,
        preferred_translation_source_languages: Iterable[str] = (
            "en",
        ),
        preserve_formatting: bool = False,
    ) -> CaptionAcquisitionResult:

        return await asyncio.to_thread(
            cls._discover_sync,
            video_id,
            requested_language,
            allow_translation,
            tuple(
                preferred_translation_source_languages
            ),
            preserve_formatting,
        )

    @classmethod
    def _discover_sync(
        cls,
        video_id: str,
        requested_language: str,
        allow_translation: bool,
        preferred_translation_source_languages: tuple[str, ...],
        preserve_formatting: bool,
    ) -> CaptionAcquisitionResult:

        requested_language = (
            cls._normalize_language(
                requested_language
            )
        )

        errors: list[
            dict[str, str]
        ] = []

        try:
            api = YouTubeTranscriptApi()

            transcript_list = api.list(
                video_id
            )

        except TranscriptsDisabled:

            return CaptionAcquisitionResult(
                status=DiscoveryStatus.NO_SOURCE,
                video_id=video_id,
                requested_language=requested_language,
                reason="TRANSCRIPTS_DISABLED",
            )

        except NoTranscriptFound:

            return CaptionAcquisitionResult(
                status=DiscoveryStatus.NO_SOURCE,
                video_id=video_id,
                requested_language=requested_language,
                reason="CAPTION_NOT_FOUND",
            )

        except Exception as exc:

            return CaptionAcquisitionResult(
                status=DiscoveryStatus.FAILED,
                video_id=video_id,
                requested_language=requested_language,
                reason="CAPTION_LIST_FAILED",
                errors=[
                    {
                        "stage": "list",
                        "error": type(exc).__name__,
                    }
                ],
            )

        # ---------------------------------------------------------
        # 1. Exact manual caption
        # ---------------------------------------------------------

        try:

            transcript = (
                transcript_list
                .find_manually_created_transcript(
                    [requested_language]
                )
            )

            return cls._fetch_result(
                transcript,
                video_id=video_id,
                requested_language=requested_language,
                source_type=(
                    TranscriptSourceType
                    .MANUAL_CAPTION
                ),
                translated=False,
                preserve_formatting=preserve_formatting,
            )

        except Exception as exc:

            errors.append(
                {
                    "stage": "manual_exact",
                    "error": type(exc).__name__,
                }
            )

        # ---------------------------------------------------------
        # 2. Exact generated caption
        # ---------------------------------------------------------

        try:

            transcript = (
                transcript_list
                .find_generated_transcript(
                    [requested_language]
                )
            )

            return cls._fetch_result(
                transcript,
                video_id=video_id,
                requested_language=requested_language,
                source_type=(
                    TranscriptSourceType
                    .GENERATED_CAPTION
                ),
                translated=False,
                preserve_formatting=preserve_formatting,
            )

        except Exception as exc:

            errors.append(
                {
                    "stage": "generated_exact",
                    "error": type(exc).__name__,
                }
            )

        # ---------------------------------------------------------
        # 3. Explicit translation fallback
        # ---------------------------------------------------------

        if allow_translation:

            candidates = (
                cls._translation_candidates(
                    transcript_list,
                    preferred_translation_source_languages,
                )
            )

            for transcript in candidates:

                try:

                    translation_languages = getattr(
                        transcript,
                        "translation_languages",
                        None,
                    ) or []

                    if not cls._translation_supported(
                        translation_languages,
                        requested_language,
                    ):
                        continue

                    translated = transcript.translate(
                        requested_language
                    )

                    result = cls._fetch_result(
                        translated,
                        video_id=video_id,
                        requested_language=requested_language,
                        source_type=(
                            TranscriptSourceType
                            .TRANSLATED_CAPTION
                        ),
                        translated=True,
                        preserve_formatting=preserve_formatting,
                    )

                    if (
                        result.status
                        == DiscoveryStatus.SUCCESS
                    ):
                        return result

                except Exception as exc:

                    errors.append(
                        {
                            "stage": "translation",
                            "source_language": str(
                                getattr(
                                    transcript,
                                    "language_code",
                                    "",
                                )
                            ),
                            "error": type(exc).__name__,
                        }
                    )

        # ---------------------------------------------------------
        # Nothing usable
        # ---------------------------------------------------------

        return CaptionAcquisitionResult(
            status=DiscoveryStatus.NO_SOURCE,
            video_id=video_id,
            requested_language=requested_language,
            reason="NO_USABLE_CAPTION",
            errors=errors,
        )

    @classmethod
    def _translation_candidates(
        cls,
        transcript_list: Any,
        preferred_languages: tuple[str, ...],
    ) -> list[Any]:

        transcripts = list(
            transcript_list
        )

        def sort_key(
            transcript: Any,
        ):

            is_generated = bool(
                getattr(
                    transcript,
                    "is_generated",
                    False,
                )
            )

            language = cls._normalize_language(
                str(
                    getattr(
                        transcript,
                        "language_code",
                        "",
                    )
                    or ""
                )
            )

            if language in preferred_languages:

                preferred_rank = (
                    preferred_languages.index(
                        language
                    )
                )

            else:

                preferred_rank = (
                    len(preferred_languages)
                )

            return (
                1 if is_generated else 0,
                preferred_rank,
                language,
            )

        return sorted(
            transcripts,
            key=sort_key,
        )

    @classmethod
    def _translation_supported(
        cls,
        translation_languages: Any,
        requested_language: str,
    ) -> bool:

        requested_language = (
            cls._normalize_language(
                requested_language
            )
        )

        for item in translation_languages:

            code = getattr(
                item,
                "language_code",
                None,
            )

            if code is None and isinstance(
                item,
                dict,
            ):
                code = item.get(
                    "language_code"
                )

            if code is None and isinstance(
                item,
                str,
            ):
                code = item

            if (
                code
                and cls._normalize_language(
                    code
                )
                == requested_language
            ):
                return True

        return False

    @classmethod
    def _fetch_result(
        cls,
        transcript: Any,
        *,
        video_id: str,
        requested_language: str,
        source_type: TranscriptSourceType,
        translated: bool,
        preserve_formatting: bool,
    ) -> CaptionAcquisitionResult:

        try:

            fetched = transcript.fetch(
                preserve_formatting=(
                    preserve_formatting
                )
            )

            raw_segments = (
                cls._to_raw_segments(
                    fetched
                )
            )

            if not raw_segments:

                return CaptionAcquisitionResult(
                    status=DiscoveryStatus.NO_SOURCE,
                    video_id=video_id,
                    requested_language=requested_language,
                    source_type=source_type,
                    reason="EMPTY_TRANSCRIPT",
                )

            return CaptionAcquisitionResult(
                status=DiscoveryStatus.SUCCESS,
                video_id=video_id,
                requested_language=requested_language,
                actual_language=(
                    str(
                        getattr(
                            transcript,
                            "language",
                            "",
                        )
                        or ""
                    )
                    or None
                ),
                actual_language_code=(
                    str(
                        getattr(
                            transcript,
                            "language_code",
                            "",
                        )
                        or ""
                    )
                    or None
                ),
                source_type=source_type,
                is_generated=bool(
                    getattr(
                        transcript,
                        "is_generated",
                        False,
                    )
                ),
                is_translatable=bool(
                    getattr(
                        transcript,
                        "is_translatable",
                        False,
                    )
                ),
                translated=translated,
                segments=raw_segments,
            )

        except Exception as exc:

            return CaptionAcquisitionResult(
                status=DiscoveryStatus.FAILED,
                video_id=video_id,
                requested_language=requested_language,
                source_type=source_type,
                translated=translated,
                reason="CAPTION_FETCH_FAILED",
                errors=[
                    {
                        "stage": "fetch",
                        "error": type(exc).__name__,
                    }
                ],
            )

    @classmethod
    def _to_raw_segments(
        cls,
        fetched: Any,
    ) -> list[dict[str, Any]]:

        # Current API.
        if hasattr(
            fetched,
            "to_raw_data",
        ):

            raw = fetched.to_raw_data()

            return [
                dict(item)
                for item in raw
            ]

        # Compatibility fallback.
        snippets = getattr(
            fetched,
            "snippets",
            fetched,
        )

        result = []

        for item in snippets:

            if isinstance(
                item,
                dict,
            ):

                result.append(
                    dict(item)
                )

            else:

                result.append(
                    {
                        "text": getattr(
                            item,
                            "text",
                            "",
                        ),
                        "start": getattr(
                            item,
                            "start",
                            0.0,
                        ),
                        "duration": getattr(
                            item,
                            "duration",
                            0.0,
                        ),
                    }
                )

        return result

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
