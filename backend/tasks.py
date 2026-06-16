import os
import uuid
import asyncio
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.video import Video, VideoStatus, SourceType
from models.transcript import Transcript
from services import storage_service, youtube_service, audio_service, whisper_service

def generate_notes_stub(transcript_path: str):
    # Stub for future LLM note generation integration
    pass

import time

async def process_video_pipeline_async(video_id: str):
    start_time = time.time()
    audio_path = None
    
    async def update_progress(percent: int, step: str, eta: int = None):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Video).where(Video.id == uuid.UUID(video_id)))
            v = result.scalar_one_or_none()
            if v:
                v.progress_percent = percent
                v.current_step = step
                if eta is not None:
                    v.estimated_time_remaining_seconds = eta
                await db.commit()
                
    async with AsyncSessionLocal() as db:
        try:
            stmt = select(Video).where(Video.id == uuid.UUID(video_id))
            result = await db.execute(stmt)
            video = result.scalar_one_or_none()
            if not video:
                return

            if video.source_type == SourceType.YOUTUBE:
                video.status = VideoStatus.PROCESSING
                await db.commit()
                
                await update_progress(10, "Fetching Video Metadata...", 5)
                # 1. Fetch Metadata
                meta_info = await youtube_service.fetch_metadata(video.youtube_url)
                video.title = meta_info["title"]
                video.duration_seconds = meta_info["duration_seconds"]
                video.thumbnail = meta_info["thumbnail"]
                video.channel_name = meta_info["channel_name"]
                await db.commit()
                
                await update_progress(30, "Downloading Captions...", 3)
                # 2. Try Fetching Captions first
                trans_info = None
                transcript_source = "whisper_audio"
                try:
                    trans_info = await youtube_service.fetch_captions(video.youtube_url, video_id)
                    transcript_source = "youtube_captions"
                    print(f"Successfully fetched YouTube captions for {video_id}")
                except Exception as e:
                    print(f"No captions found or failed to fetch for {video_id}, falling back to audio download: {e}")
                
                # 3. Fallback to Audio Download & Whisper
                if not trans_info:
                    eta = int((video.duration_seconds or 300) * 0.1)  # rough download estimate
                    await update_progress(40, "Downloading Audio Stream...", eta)
                    dl_info = await youtube_service.download_video(video.youtube_url, video_id)
                    video.video_path = dl_info["path"]
                    await db.commit()

                    await update_progress(50, "Extracting Audio Track...", eta)
                    audio_path = await audio_service.extract_audio(video.video_path, video_id)

                    video.status = VideoStatus.TRANSCRIBING
                    await db.commit()
                    
                    eta_transcribe = int((video.duration_seconds or 300) * 0.4)
                    await update_progress(60, "Transcribing with Whisper AI...", eta_transcribe)
                    trans_info = await whisper_service.transcribe(audio_path, video_id)
            else:
                video.status = VideoStatus.PROCESSING
                await db.commit()
                
                await update_progress(40, "Extracting Audio Track...", 10)
                audio_path = await audio_service.extract_audio(video.video_path, video_id)

                video.status = VideoStatus.TRANSCRIBING
                await db.commit()
                
                await update_progress(60, "Transcribing with Whisper AI...", 120)
                trans_info = await whisper_service.transcribe(audio_path, video_id)
                transcript_source = "manual_upload"

            await update_progress(90, "Finalizing Database Records...", 2)
            transcript = Transcript(
                video_id=video.id,
                transcript_path=trans_info["json_path"],
                language=trans_info["language"],
                word_count=trans_info["word_count"],
                source=transcript_source
            )
            db.add(transcript)
            
            # Generate Notes
            await update_progress(95, "Generating Notes...", 5)
            generate_notes_stub(trans_info["json_path"])
            
            processing_time = int(time.time() - start_time)
            video.status = VideoStatus.COMPLETED
            video.progress_percent = 100
            video.current_step = "Completed"
            video.processing_time_seconds = processing_time
            video.estimated_time_remaining_seconds = 0
            await db.commit()
            print(f"Pipeline completed for video {video_id} in {processing_time}s")
            
        except Exception as e:
            stmt = select(Video).where(Video.id == uuid.UUID(video_id))
            result = await db.execute(stmt)
            video = result.scalar_one_or_none()
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = str(e)
                await db.commit()
            print(f"Pipeline failed for video {video_id}: {e}")
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    print(f"Cleaned up temporary audio file: {audio_path}")
                except Exception as cleanup_err:
                    print(f"Failed to cleanup audio file {audio_path}: {cleanup_err}")
