import asyncio
import logging
import traceback
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.utils import parse_video_id
from models.video import Video, VideoStatus, SourceType
from models.transcript import Transcript, TranscriptSource
from services.youtube import youtube_service
from services.audio import audio_service
from services.whisper_service import whisper_service
from services.vision.pipeline import vision_pipeline
from services.content_intelligence import content_intelligence
from services.vector_store import vector_store
from services.merge_service import merge_service
import json
from models.vision import VideoFrame, OCRResult, FrameScore

logger = logging.getLogger(__name__)

async def process_video_pipeline_async(video_id_str: str):
    """
    Background orchestrator that runs the entire pipeline for a video.

    Pipeline steps:
      1. YouTube Download (if applicable)
      2. Audio Extraction (WAV)
      3. Whisper Transcription
      4. Vision Pipeline (frames + OCR + scoring)
      5. Content Intelligence — Phase 1–2 (topics, notes, concepts, objectives)
      6. Content Intelligence — Phase 3–4 (definitions, steps, applications, misconceptions)
      7. Content Intelligence — Phase 5 (assessments, examples, learning path)
      8. Content Intelligence — Phase 7 (QA + mind map + glossary)
      9. Markdown Generation (merge service)
     10. Vector Embeddings for Search
     11. Complete
    """
    video_id = parse_video_id(video_id_str)
    
    async def update_status(db: AsyncSession, status: VideoStatus, current_step: str, progress: int):
        # Fetch fresh to avoid stale object
        res = await db.execute(select(Video).where(Video.id == video_id))
        video = res.scalar_one_or_none()
        if video:
            video.status = status
            video.current_step = current_step
            video.progress_percent = progress
            await db.commit()
            
    async def set_error(db: AsyncSession, error_message: str):
        res = await db.execute(select(Video).where(Video.id == video_id))
        video = res.scalar_one_or_none()
        if video:
            video.status = VideoStatus.FAILED
            video.error_message = error_message
            await db.commit()

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            
            if not video:
                logger.error("Video %s not found in database. Aborting pipeline.", video_id_str)
                return

            # ── STEP 1: YouTube Download (if applicable) ─────────────────────
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

            # ── STEP 2: Extract Audio ──────────────────────────────────────────
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
                source=TranscriptSource.WHISPER_AUDIO
            )
            db.add(transcript)
            await db.commit()
            
            # Cleanup audio file to save disk space
            if os.path.exists(audio_path):
                os.remove(audio_path)

            # ── STEP 4: Vision Pipeline ───────────────────────────────────────
            await update_status(db, VideoStatus.EXTRACTING_FRAMES, "Running Vision Pipeline", 60)
            # Handles scene detection, frame extraction, OCR, transcript matching,
            # scoring and persistence
            vision_stats = await vision_pipeline.run(video_id_str, video.video_path)
            logger.info("Vision Pipeline Stats: %s", vision_stats)

            # ── STEP 5: Load Transcript + Frames for Intelligence Phases ─────
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Loading transcript and frames", 70)
            
            # Fetch transcript JSON
            try:
                with open(transcript.transcript_path, 'r', encoding='utf-8') as f:
                    transcript_segments = json.load(f)
            except Exception as e:
                logger.error("Failed to read transcript for video %s: %s", video_id_str, e)
                transcript_segments = []

            # Fetch selected keyframes with OCR
            f_result = await db.execute(
                select(VideoFrame, OCRResult)
                .join(FrameScore, FrameScore.frame_id == VideoFrame.id)
                .join(OCRResult, OCRResult.frame_id == VideoFrame.id, isouter=True)
                .where(VideoFrame.video_id == parse_video_id(video_id_str), FrameScore.is_selected == True)
                .order_by(VideoFrame.timestamp_ms.asc())
            )
            rows = f_result.all()
            frames_data = []
            for frame, ocr in rows:
                frames_data.append({
                    "path": frame.frame_path,
                    "time_sec": frame.timestamp_ms / 1000.0,
                    "ocr": ocr.clean_text if ocr and ocr.clean_text else None
                })

            # ── STEP 6: Phase 1–2 Content Intelligence ───────────────────────
            await update_status(db, VideoStatus.DETECTING_TOPICS, "Generating AI Notes & Topics", 72)
            topics_data = await content_intelligence.generate_topics_and_notes(transcript_segments, frames_data)

            await update_status(db, VideoStatus.DETECTING_TOPICS, "Extracting Concepts & Keywords", 74)
            concepts_data = await content_intelligence.extract_concepts_and_keywords(transcript_segments)

            await update_status(db, VideoStatus.DETECTING_TOPICS, "Detecting Learning Objectives", 76)
            objectives_data = await content_intelligence.detect_learning_objectives(transcript_segments)

            await update_status(db, VideoStatus.DETECTING_TOPICS, "Detecting Prerequisites & Dependencies", 77)
            prerequisites_data = await content_intelligence.detect_prerequisites_and_dependencies(transcript_segments)

            await update_status(db, VideoStatus.DETECTING_TOPICS, "Classifying Difficulty", 78)
            difficulty_data = await content_intelligence.classify_difficulty(transcript_segments)

            # ── STEP 7: Phase 3–4 Knowledge Enrichment ───────────────────────
            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Definitions", 79)
            definitions_data = await content_intelligence.generate_definitions(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Step-by-Step Explanations", 80)
            step_by_step_data = await content_intelligence.generate_step_by_step_explanations(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Real-World Applications", 81)
            applications_data = await content_intelligence.generate_real_world_applications(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Examples & Analogies", 82)
            examples_data = await content_intelligence.generate_examples(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Detecting Misconceptions & Edge Cases", 83)
            misconceptions_data = await content_intelligence.detect_misconceptions_and_edge_cases(transcript_segments)

            # ── STEP 8: Phase 5 & Legacy — Assessments, Support, Glossary ───
            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Quizzes & Flashcards", 84)
            assessments_data = await content_intelligence.generate_assessments(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Learning Support", 85)
            support_data = await content_intelligence.generate_learning_support(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Learning Path", 86)
            learning_path_data = await content_intelligence.generate_learning_path(transcript_segments)

            await update_status(db, VideoStatus.GENERATING_NOTES, "Extracting Glossary", 87)
            glossary_data = await content_intelligence.generate_glossary(transcript_segments)

            # ── STEP 9: Phase 7 — QA + Mind Map ──────────────────────────────
            await update_status(db, VideoStatus.GENERATING_NOTES, "Running QA Fact Verification", 88)
            qa_data = await content_intelligence.verify_facts(transcript_segments, topics_data)
            
            await update_status(db, VideoStatus.GENERATING_NOTES, "Generating Mind Map", 90)
            mind_map_data = await content_intelligence.generate_mind_map(transcript_segments)

            # ── STEP 10: Generate Final Markdown ─────────────────────────────
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
                # Phase 2 enrichment
                concepts_data=concepts_data,
                objectives_data=objectives_data,
                prerequisites_data=prerequisites_data,
                difficulty_data=difficulty_data,
                # Phase 3-4 enrichment
                definitions_data=definitions_data,
                step_by_step_data=step_by_step_data,
                applications_data=applications_data,
                misconceptions_data=misconceptions_data,
                # Phase 5 enrichment
                learning_path_data=learning_path_data,
            )
            
            if not merged_md_path:
                logger.warning("Failed to generate merged markdown for video %s", video_id_str)

            # ── STEP 11: Generate Vector Embeddings for Search ────────────────
            if merged_md_path and os.path.exists(merged_md_path):
                await update_status(db, VideoStatus.EXPORTING, "Generating Vector Embeddings", 97)
                with open(merged_md_path, "r", encoding="utf-8") as f:
                    final_md_text = f.read()
                await vector_store.build_index(video_id_str, final_md_text)

            # ── STEP 12: Complete ─────────────────────────────────────────────
            await update_status(db, VideoStatus.COMPLETED, "Completed", 100)
            logger.info("Pipeline completed successfully for video %s", video_id_str)

    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        async with AsyncSessionLocal() as db:
            await set_error(db, str(e))
