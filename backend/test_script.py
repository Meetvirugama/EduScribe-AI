import asyncio
import uuid
import sys
import os
import logging
from dotenv import load_dotenv

# load env vars
os.environ["ENABLE_STT_FALLBACK"] = "true"
load_dotenv(os.path.join(os.path.abspath("backend"), ".env"))

# add backend path to sys.path
sys.path.append(os.path.abspath("backend"))

from core.database import AsyncSessionLocal
from models.user import User
from models.video import Video, SourceType
from pipeline.orchestrator import process_video_pipeline_async

logging.basicConfig(level=logging.INFO)

async def test_full_pipeline():
    url = "https://www.youtube.com/watch?v=vh525RjO6C0"
    
    async with AsyncSessionLocal() as db:
        # Get or create dummy user
        from sqlalchemy import select
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                google_id="test_google_id",
                email="test_full_project@example.com",
                name="Test User"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create dummy video
        vid_uuid = uuid.uuid4()
        video = Video(
            id=vid_uuid,
            user_id=user.id,
            title="Test Video",
            source_type=SourceType.YOUTUBE,
            youtube_url=url,
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)
        
        print(f"Created Video DB record with ID: {vid_uuid}")

    # 2. Run Pipeline
    print(f"Starting pipeline for video ID: {vid_uuid}")
    await process_video_pipeline_async(str(vid_uuid))
    print("Pipeline completed!")
    from core.config import settings
    output_dir = os.path.join(settings.OUTPUT_DIR, str(vid_uuid))
    print(f"Data saved continuously to: {output_dir}")
    print(f"Check {output_dir}/detailed_notes.md for the final output!")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
