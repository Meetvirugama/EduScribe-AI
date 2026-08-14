import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.video import Video

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Video).order_by(Video.created_at.desc()).limit(1)
        )
        video = result.scalar_one_or_none()
        if video:
            print(f"Latest Video: {video.id}")
            print(f"Title: {video.title}")
            print(f"Status: {video.status}")
            print(f"Current Step: {video.current_step}")
            print(f"Progress: {video.progress_percent}%")
            if video.error_message:
                print(f"Error: {video.error_message}")
        else:
            print("No videos found in database.")

if __name__ == "__main__":
    asyncio.run(main())
