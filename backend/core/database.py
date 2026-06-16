from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

# Asyncpg connection string requires postgresql+asyncpg:// instead of postgresql://
# We also need to strip ?sslmode=require because asyncpg doesn't accept it as a kwarg.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").split("?")[0]

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    # SSL requirement for Neon
    connect_args={"ssl": True} if "neon.tech" in SQLALCHEMY_DATABASE_URL else {}
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
