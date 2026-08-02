from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

# Asyncpg connection string requires postgresql+asyncpg:// instead of postgresql://
# We also need to strip ?sslmode=require because asyncpg doesn't accept it as a kwarg.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").split("?")[0]

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    # Connection pool tuning: default pool_size=5 bottlenecks under concurrent load.
    # pool_size=10: Maintain 10 persistent connections ready for immediate use.
    # max_overflow=20: Allow up to 20 extra connections beyond pool_size under burst load.
    # pool_recycle=1800: Recycle connections every 30 min to avoid stale connection errors
    #   (common with managed DBs like Neon that close idle connections after a timeout).
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
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
