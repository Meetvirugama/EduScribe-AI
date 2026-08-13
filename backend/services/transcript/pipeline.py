import logging
from typing import Dict, Any
from .url_normalizer import URLNormalizer
from .metadata import MetadataService
from .captions import CaptionService
from .parser import ParserService
from .canonicalizer import CanonicalizerService
from .exporter import ExporterService

logger = logging.getLogger(__name__)


class TranscriptPipeline:
    """
    End-to-End Orchestrator for Phase 1 Transcript Processing.
    Implements: URL Normalization -> Metadata Check -> Caption Discovery ->
    Caption Acquisition -> Raw Artifact Save -> Parser -> Canonicalization -> Export.
    """

    @staticmethod
    async def process_video(
            url: str, requested_language: str = "en") -> Dict[str, Any]:
        logger.info(f"Starting Transcript Pipeline for: {url}")

        # 1. URL Normalization
        normalized = URLNormalizer.normalize(url)
        video_id = normalized["video_id"]
        logger.info(f"Normalized Video ID: {video_id}")

        # 2. Metadata Check (Ensures video is accessible)
        logger.info("Fetching Metadata to ensure accessibility...")
        metadata = await MetadataService.fetch_metadata(url)
        logger.info(f"Metadata verified. Title: {metadata['title']}")

        # 3 & 4. Caption Discovery & Acquisition (saves raw artifact
        # internally)
        logger.info(
            f"Discovering and acquiring captions for language: {requested_language}...")
        raw_payload = CaptionService.discover_and_acquire(
            video_id, requested_language)
        logger.info(
            f"Acquired raw payload. Source type: {raw_payload['source_type']}")

        # 5. Parser
        logger.info("Parsing raw segments...")
        raw_segments = ParserService.parse(raw_payload)
        logger.info(f"Successfully parsed {len(raw_segments)} segments.")

        # 6. Canonicalization
        logger.info("Canonicalizing text (normalizing and structuring)...")
        canonical_transcript = CanonicalizerService.canonicalize(
            raw_payload, raw_segments)

        # (Metadata merged into CanonicalTranscript)
        canonical_transcript.metadata = metadata

        # 7. Export
        logger.info("Exporting canonical transcript to TXT, SRT, VTT, JSON...")
        exported_paths = ExporterService.export_all(canonical_transcript)

        logger.info("Pipeline Phase 1 Complete!")
        return {
            "status": "COMPLETED",
            "video_id": video_id,
            "source_type": canonical_transcript.source_type,
            "segment_count": len(canonical_transcript.segments),
            "artifacts": exported_paths
        }
