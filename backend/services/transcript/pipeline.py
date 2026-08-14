from __future__ import annotations

from typing import Any

from .captions import (
    CaptionDiscovery,
)

from .canonicalizer import (
    Canonicalizer,
)

from .metadata import (
    MetadataAcquisition,
)

from .models import (
    DiscoveryStatus,
)

from .quality import (
    QualityEngine,
)

from .url_normalizer import (
    URLNormalizer,
)

from .validator import (
    TranscriptValidator,
)


class TranscriptPipeline:

    @classmethod
    async def process(
        cls,
        url: str,
        *,
        requested_language: str = "en",
        allow_translation: bool = False,
        translation_source_languages: tuple[
            str, ...
        ] = ("en",),
        metadata_cookie_file: str | None = None,
        metadata_player_clients: tuple[
            str, ...
        ] | None = None,
        max_duration_seconds: int | None = None,
    ) -> dict[str, Any]:

        # -----------------------------------------------------
        # 1. URL
        # -----------------------------------------------------

        normalized = (
            URLNormalizer
            .validate_and_normalize(
                url
            )
        )

        video_id = normalized[
            "video_id"
        ]

        # -----------------------------------------------------
        # 2. Metadata
        # -----------------------------------------------------

        metadata = (
            await MetadataAcquisition
            .fetch_metadata(
                url,
                cookie_file=(
                    metadata_cookie_file
                ),
                player_clients=(
                    metadata_player_clients
                ),
                max_duration_seconds=(
                    max_duration_seconds
                ),
            )
        )

        # -----------------------------------------------------
        # 3. Caption discovery
        # -----------------------------------------------------

        discovery = (
            await CaptionDiscovery
            .discover_and_acquire(
                video_id,
                requested_language=(
                    requested_language
                ),
                allow_translation=(
                    allow_translation
                ),
                preferred_translation_source_languages=(
                    translation_source_languages
                ),
            )
        )

        # -----------------------------------------------------
        # 4. No caption
        # -----------------------------------------------------

        if (
            discovery.status
            != DiscoveryStatus.SUCCESS
        ):

            return {
                "status": discovery.status.value,
                "video_id": video_id,
                "metadata": metadata,
                "discovery": (
                    discovery.to_dict()
                ),
                "requires_stt_fallback": (
                    discovery.reason
                    in {
                        "NO_USABLE_CAPTION",
                        "CAPTION_NOT_FOUND",
                        "TRANSCRIPTS_DISABLED",
                        "EMPTY_TRANSCRIPT",
                    }
                ),
            }

        # -----------------------------------------------------
        # 5. Canonicalization
        # -----------------------------------------------------

        source_type = (
            discovery.source_type.value
            if discovery.source_type
            else None
        )

        if source_type == (
            "manual_caption"
        ):

            source = (
                "youtube_manual_caption"
            )

        elif source_type == (
            "generated_caption"
        ):

            source = (
                "youtube_generated_caption"
            )

        else:

            source = (
                "youtube_translated_caption"
            )

        canonical = (
            Canonicalizer
            .canonicalize_youtube_captions(
                discovery.segments,
                (
                    discovery.actual_language_code
                    or requested_language
                ),
                source=source,
            )
        )

        # -----------------------------------------------------
        # 6. Validation
        # -----------------------------------------------------

        validation = (
            TranscriptValidator.validate(
                canonical,
                media_duration=(
                    metadata.get(
                        "duration_seconds"
                    )
                ),
            )
        )

        # -----------------------------------------------------
        # 7. Quality
        # -----------------------------------------------------

        quality = (
            QualityEngine.assess(
                validation.segments,
                media_duration=(
                    metadata.get(
                        "duration_seconds"
                    )
                ),
                requested_language=(
                    requested_language
                ),
                actual_language=(
                    discovery.actual_language_code
                ),
                source_type=source_type,
                validation_issues=[
                    issue.to_dict() if hasattr(issue, "to_dict") else issue
                    for issue
                    in validation.issues
                ],
            )
        )

        # -----------------------------------------------------
        # 8. Final result
        # -----------------------------------------------------

        return {
            "status": (
                "SUCCESS"
                if validation.valid
                else "QUALITY_REVIEW"
            ),
            "video_id": video_id,
            "metadata": metadata,
            "discovery": (
                discovery.to_dict()
            ),
            "segments": (
                validation.segments
            ),
            "validation": (
                validation.to_dict() if hasattr(validation, "to_dict") else validation
            ),
            "quality": quality,
        }
