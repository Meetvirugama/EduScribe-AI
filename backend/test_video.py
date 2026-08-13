import asyncio
import uuid
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.video import Video, SourceType, VideoStatus
from pipeline.orchestrator import process_video_pipeline_async

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User))
        user = res.scalars().first()
        if not user:
            print("No user found in DB. Creating one...")
            user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="test", is_active=True)
            db.add(user)
            await db.commit()
            
        video_id = uuid.uuid4()
        video = Video(
            id=video_id,
            user_id=str(user.id),
            title="Live Day 1- Introduction To Machine Learning Algorithms",
            source_type=SourceType.UPLOAD,
            video_path="/Users/meetvirugama/Desktop/EduScribe-AI/Live Day 1- Introduction To Machine Learning Algorithms For Data Science.mp4",
            retention_days=7,
            status=VideoStatus.UPLOADING,
        )
        db.add(video)
        await db.commit()
        print(f"Inserted video with ID: {video_id}")
        
    print("Starting pipeline...")
    await process_video_pipeline_async(str(video_id))
    print("Pipeline finished.")

if __name__ == "__main__":
    asyncio.run(main())
