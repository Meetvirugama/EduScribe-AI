import asyncio
import logging
import traceback
import os
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.utils import parse_video_id
from models.video import Video, VideoStatus, SourceType
from models.transcript import Transcript, TranscriptSource
from services.youtube import youtube_service
from services.audio import audio_service, whisper_service
from services.vision.pipeline import vision_pipeline
from services.content.intelligence import content_intelligence
from services.rag.pipeline import vector_store
from services.content.merge import merge_service
from services.rag.structure_detector import structure_detector
from services.rag.context_optimizer import context_optimizer
from services.quality.evaluator import quality_evaluator
from services.content.formula import FormulaService
from services.content.interview import InterviewService
from services.content.revision import RevisionService
import json
from models.vision import VideoFrame, OCRResult, FrameScore

logger = logging.getLogger(__name__)


async def _set_video_error(video_id, error_message: str) -> None:
    """
    Open a fresh DB session and mark the video as FAILED.

    ISSUE-14: This function opens its own session instead of reusing the
    pipeline's session (which has already exited its `async with` block by
    the time the outer except clause runs).
    """
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Video).where(Video.id == video_id))
            video = res.scalar_one_or_none()
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = str(error_message)[:2000]  # cap length
                await db.commit()
    except Exception as db_err:
        logger.error("Could not persist error state for video %s: %s", video_id, db_err)


async def process_video_pipeline_async(video_id_str: str):
    """
    Background orchestrator that runs the entire pipeline for a video.

    Pipeline steps:
      1. YouTube Download (if applicable)
      2. Audio Extraction (WAV)
      3. Whisper Transcription
      4. Vision Pipeline (frames + OCR + scoring)
      5. Phase 1: Topics & Notes generation
      6. Phase 2: Concepts, Objectives, Prerequisites, Difficulty (PARALLEL — PERF-01)
      7. Phase 3–4: Definitions, Step-by-step, Applications, Examples, Misconceptions (PARALLEL)
      8. Phase 5: Assessments, Learning Support, Learning Path, Glossary (PARALLEL)
      9. Phase 7: QA Fact Verification + Mind Map (PARALLEL)
     10. Markdown Generation (merge service)
     11. Vector Embeddings for Search
     12. Complete

    ISSUE-14: Error handler opens a fresh DB session — the main session has
              already exited its context manager by the time except runs.
    PERF-01:  Independent LLM calls within each phase run concurrently via
              asyncio.gather, reducing total latency from ~75s to ~20s.
    """
    video_id = parse_video_id(video_id_str)

    async def update_status(db: AsyncSession, status: VideoStatus, current_step: str, progress: int):
        res = await db.execute(select(Video).where(Video.id == video_id))
        video = res.scalar_one_or_none()
        if video:
            video.status = status
            video.current_step = current_step
            video.progress_percent = progress
            await db.commit()

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()

            if not video:
                logger.error("Video %s not found in database. Aborting pipeline.", video_id_str)
                return

            # IMP-07: record when processing starts
            video.processing_started_at = datetime.now(tz=timezone.utc)
            await db.commit()

            # ── STEP 1: YouTube Download (if applicable) ──────────────────────
            if video.source_type == SourceType.YOUTUBE:
                await update_status(db, VideoStatus.UPLOADING, "Downloading YouTube Video", 10)
                yt_info = await youtube_service.download_video(video.youtube_url, video_id_str)
                video.video_path = yt_info["path"]
                video.title = yt_info["title"]
                video.duration_seconds = yt_info["duration_seconds"]
                video.thumbnail = yt_info["thumbnail"]
                video.channel_name = yt_info["channel_name"]
                await db.commit()

            if not video.video_path or not os.path.exists(video.video_path):
                raise Exception(f"Video file not found at path: {video.video_path}")

            # ── STEP 2: Extract Audio ─────────────────────────────────────────
            await update_status(db, VideoStatus.EXTRACTING_AUDIO, "Extracting Audio (WAV)", 20)
            audio_path = await audio_service.extract_audio(video.video_path, video_id_str)

            # ── STEP 3: Transcribe Audio (Whisper) ────────────────────────────
            await update_status(db, VideoStatus.TRANSCRIBING, "Transcribing Audio (faster-whisper)", 40)
            transcript_res = await whisper_service.transcribe(audio_path, video_id_str)

            # Save Transcript to DB
            transcript = Transcript(
                video_id=video_id,
                transcript_path=transcript_res["json_path"],
                language=transcript_res["language"],
                word_count=transcript_res["word_count"],
                source=TranscriptSource.WHISPER_AUDIO,
            )
            db.add(transcript)
            await db.commit()

            # Cleanup audio file to save disk space
            if os.path.exists(audio_path):
                os.remove(audio_path)

            # ── STEP 4: Vision Pipeline ───────────────────────────────────────
            await update_status(db, VideoStatus.EXTRACTING_FRAMES, "Running Vision Pipeline", 60)
            vision_stats = await vision_pipeline.run(video_id_str, video.video_path)
            logger.info("Vision Pipeline Stats: %s", vision_stats)

            # ── Load Transcript + Frames for Intelligence Phases ──────────────
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Loading transcript and frames", 70)

            try:
                with open(transcript.transcript_path, "r", encoding="utf-8") as f:
                    transcript_segments = json.load(f)
            except Exception as e:
                logger.error("Failed to read transcript for video %s: %s", video_id_str, e)
                transcript_segments = []

            # Fetch selected keyframes with OCR
            f_result = await db.execute(
                select(VideoFrame, OCRResult)
                .join(FrameScore, FrameScore.frame_id == VideoFrame.id)
                .join(OCRResult, OCRResult.frame_id == VideoFrame.id, isouter=True)
                .where(
                    VideoFrame.video_id == parse_video_id(video_id_str),
                    FrameScore.is_selected == True,
                )
                .order_by(VideoFrame.timestamp_ms.asc())
            )
            rows = f_result.all()
            frames_data = [
                {
                    "path": frame.frame_path,
                    "time_sec": frame.timestamp_ms / 1000.0,
                    "ocr": ocr.clean_text if ocr and ocr.clean_text else None,
                }
                for frame, ocr in rows
            ]

            # ── STEP 4.5: Detect Lecture Structure (Issue #10) ───────────────
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Detecting lecture structure", 68)
            try:
                lecture_structure = await structure_detector.detect(
                    transcript_segments,
                    frames_data=frames_data,
                    llm_manager=content_intelligence.llm_manager,
                )
                detected_topics = lecture_structure.as_topics()
                logger.info(
                    "StructureDetector: %d sections detected for video %s",
                    len(lecture_structure.sections), video_id_str,
                )
            except Exception as e:
                logger.warning("Structure detection failed for %s: %s — continuing without it", video_id_str, e)
                lecture_structure = None
                detected_topics = None

            # ── STEP 5: Phase 1 — Topics & Notes ─────────────────────────────
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Generating AI Notes & Topics", 72)
            topics_data = await content_intelligence.generate_topics_and_notes(transcript_segments, frames_data)

            # ── STEP 6: Phase 2 — PARALLEL intelligence extraction ────────────
            # PERF-01: These 4 calls are independent — run concurrently.
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Extracting Intelligence (Phase 2)", 74)
            (
                concepts_data,
                objectives_data,
                prerequisites_data,
                difficulty_data,
            ) = await asyncio.gather(
                content_intelligence.extract_concepts_and_keywords(transcript_segments),
                content_intelligence.detect_learning_objectives(transcript_segments),
                content_intelligence.detect_prerequisites_and_dependencies(transcript_segments),
                content_intelligence.classify_difficulty(transcript_segments),
            )

            # ── STEP 7: Phase 3–4 — PARALLEL knowledge enrichment ────────────
            await update_status(db, VideoStatus.GENERATING_NOTES, "Enriching Knowledge (Phase 3-4)", 80)
            (
                definitions_data,
                step_by_step_data,
                applications_data,
                examples_data,
                misconceptions_data,
            ) = await asyncio.gather(
                content_intelligence.generate_definitions(transcript_segments),
                content_intelligence.generate_step_by_step_explanations(transcript_segments),
                content_intelligence.generate_real_world_applications(transcript_segments),
                content_intelligence.generate_examples(transcript_segments),
                content_intelligence.detect_misconceptions_and_edge_cases(transcript_segments),
            )

            # ── STEP 8: Phase 5 — PARALLEL assessments & support ─────────────
            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Assessments (Phase 5)", 85)
            (
                assessments_data,
                support_data,
                learning_path_data,
                glossary_data,
                formula_data,
                interview_data,
                revision_data,
            ) = await asyncio.gather(
                content_intelligence.generate_assessments(transcript_segments),
                content_intelligence.generate_learning_support(transcript_segments),
                content_intelligence.generate_learning_path(transcript_segments),
                content_intelligence.generate_glossary(transcript_segments),
                FormulaService(content_intelligence.llm_manager).generate_formula_sheet(transcript_segments, frames_data),
                InterviewService(content_intelligence.llm_manager).generate_interview_questions(transcript_segments),
                RevisionService(content_intelligence.llm_manager).generate_revision_sheet(transcript_segments),
            )

            # ── STEP 9: Phase 7 — PARALLEL QA & mind map ─────────────────────
            await update_status(db, VideoStatus.GENERATING_NOTES, "Running QA & Mind Map", 88)
            (
                qa_data,
                mind_map_data,
            ) = await asyncio.gather(
                content_intelligence.verify_facts(transcript_segments, topics_data),
                content_intelligence.generate_mind_map(transcript_segments),
            )

            # ── STEP 10: Generate Final Markdown ──────────────────────────────
            await update_status(db, VideoStatus.EXPORTING, "Compiling Markdown", 92)
            merged_md_path = await merge_service.generate_merged_markdown(
                video_id=video_id_str,
                topics_data=topics_data,
                assessments_data=assessments_data,
                examples_data=examples_data,
                support_data=support_data,
                glossary_data=glossary_data,
                qa_data=qa_data,
                mind_map_data=mind_map_data,
                concepts_data=concepts_data,
                objectives_data=objectives_data,
                prerequisites_data=prerequisites_data,
                difficulty_data=difficulty_data,
                definitions_data=definitions_data,
                step_by_step_data=step_by_step_data,
                applications_data=applications_data,
                misconceptions_data=misconceptions_data,
                learning_path_data=learning_path_data,
                formula_data=formula_data,
                interview_data=interview_data,
                revision_data=revision_data,
            )

            if not merged_md_path:
                logger.warning("Failed to generate merged markdown for video %s", video_id_str)

            # ── STEP 10.5: Quality Evaluation (Issue #8) ──────────────────────
            quality_score = None
            if merged_md_path and os.path.exists(merged_md_path):
                try:
                    with open(merged_md_path, "r", encoding="utf-8") as _f:
                        notes_text = _f.read()
                    quality_report = quality_evaluator.evaluate(
                        notes_text=notes_text,
                        transcript_segments=transcript_segments,
                        topics_data=topics_data,
                    )
                    quality_score = quality_report.overall_score
                    if quality_report.warnings:
                        for w in quality_report.warnings:
                            logger.warning("[QA] video=%s: %s", video_id_str, w)
                except Exception as e:
                    logger.warning("Quality evaluation failed for %s: %s", video_id_str, e)

            # ── STEP 11: Build RAG Vector Index (Issue #1-4: full pipeline) ───
            await update_status(db, VideoStatus.EXPORTING, "Building RAG Vector Index", 97)
            try:
                embedded_count = await vector_store.build_index(
                    video_id_str,
                    transcript_segments=transcript_segments,
                    frames_data=frames_data,
                    topics=detected_topics,  # enables topic-based chunking
                )
                logger.info(
                    "RAG index built with %d chunks for video %s",
                    embedded_count, video_id_str,
                )
            except Exception as e:
                logger.error("RAG index build failed for %s: %s", video_id_str, e)
                # Non-fatal: notes are already generated, search just won't work

            # ── STEP 12: Compute processing time (IMP-07) ─────────────────────
            processing_time = None
            if video.processing_started_at:
                elapsed = datetime.now(tz=timezone.utc) - video.processing_started_at.replace(tzinfo=timezone.utc)
                processing_time = int(elapsed.total_seconds())

            # ── STEP 13: Complete ──────────────────────────────────────────────
            res = await db.execute(select(Video).where(Video.id == video_id))
            video = res.scalar_one_or_none()
            if video:
                video.status = VideoStatus.COMPLETED
                video.current_step = "Completed"
                video.progress_percent = 100
                if processing_time is not None:
                    video.processing_time_seconds = processing_time
                await db.commit()

            logger.info(
                "Pipeline completed for video %s in %ss",
                video_id_str,
                processing_time or "N/A",
            )

    except Exception as e:
        # ISSUE-14: Open a fresh session — the `async with AsyncSessionLocal()`
        # block above has already exited when we reach this except clause.
        logger.error(
            "Pipeline failed for video %s: %s\n%s",
            video_id_str,
            str(e),
            traceback.format_exc(),
        )
        await _set_video_error(video_id, str(e))
