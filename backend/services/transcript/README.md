# Transcript Ingestion Pipeline

This package handles the robust, end-to-end extraction, canonicalization, validation, and export of video transcripts.

## Architecture

```text
                     URL
                      |
                      v
              URLNormalizer
                      |
                      v
             MetadataAcquisition
                      |
                      v
             CaptionDiscovery
                      |
              +-------+-------+
              |               |
           SUCCESS         NO_SOURCE
              |               |
              v               v
       Canonicalizer     Authorized STT
              |               |
              +-------+-------+
                      |
                      v
             TranscriptValidator
                      |
                      v
               QualityEngine
                      |
          +-----------+-----------+
          |                       |
        HIGH/MEDIUM              LOW
          |                       |
          v                       v
       Export                  Review
          |
          v
    TXT/SRT/VTT/JSON
          |
          v
    Artifact Manifest
          |
          v
       COMPLETE
```

## Modules

*   `pipeline.py`: The core orchestrator (`TranscriptPipeline`) that seamlessly links all engines.
*   `url_normalizer.py`: Validates and extracts canonical video IDs.
*   `metadata.py`: Fetches foundational video metadata via yt-dlp.
*   `captions.py`: The `CaptionDiscovery` engine handling YouTube caption ingestion and translation strategies.
*   `canonicalizer.py`: Normalizes raw transcript data (from YouTube or STT) into strictly typed `TranscriptSegment` models.
*   `validator.py`: Evaluates `TranscriptSegment` streams for overlaps, duplicates, out-of-bounds bounds, and calculates duration coverage.
*   `quality.py`: `QualityEngine` uses heuristics from the validator to score and assess final transcript reliability.
*   `exporter.py`: Atomically saves outputs into standard formats (`txt`, `srt`, `vtt`, `json`) and generates SHA-256 artifact manifests.
*   `models.py` & `errors.py`: The underlying strictly typed dataclasses and custom exception hierarchies.
