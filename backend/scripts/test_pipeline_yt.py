import asyncio
import uuid
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from models.user import User
from models.video import Video, SourceType, VideoStatus
from pipeline.orchestrator import process_video_pipeline_async

async def main():
    yt_url = "https://www.youtube.com/watch?v=D1eL1EnxXXQ"
    print(f"Testing pipeline for {yt_url}")
    
    async with AsyncSessionLocal() as db:
        # Create a mock user
        user_id = str(uuid.uuid4())
        mock_user = User(
            id=uuid.UUID(user_id),
            google_id=f"google_{user_id}",
            email=f"test_{user_id}@example.com",
            name="Test User",
            is_admin=False
        )
        db.add(mock_user)
        
        # Create a mock video
        video_id = str(uuid.uuid4())
        video = Video(
            id=uuid.UUID(video_id),
            user_id=user_id,
            title="Pipeline Test",
            source_type=SourceType.YOUTUBE,
            youtube_url=yt_url,
            retention_days=7,
            status=VideoStatus.UPLOADING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(video)
        await db.commit()
        
    print(f"Created Video ID: {video_id}. Starting pipeline...")
    await process_video_pipeline_async(video_id)
    print("Pipeline finished.")

if __name__ == "__main__":
    asyncio.run(main())
