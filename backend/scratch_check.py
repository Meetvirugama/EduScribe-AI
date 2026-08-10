import asyncio
from core.database import AsyncSessionLocal
from models.video import Video
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Video.id, Video.status, Video.error_message))
        for r in res.all():
            print(f"ID: {r.id}, Status: {r.status}, Error: {r.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
