from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from core.config import settings

# LOW-004: Strip only the query-string parameters that asyncpg cannot accept as
# kwargs (e.g. sslmode, which PostgreSQL connection strings often include).
# The previous .split("?")[0] was overly broad — it discarded ALL parameters,
# including legitimate ones (e.g. application_name, channel_binding).
def _build_asyncpg_url(raw_url: str) -> str:
    # Convert driver scheme
    url = raw_url.replace("postgresql://", "postgresql+asyncpg://").replace(
        "postgres://", "postgresql+asyncpg://"
    )
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    # Parameters asyncpg does not support as URL kwargs
    _ASYNCPG_INCOMPATIBLE = {"sslmode"}
    filtered = {k: v for k, v in params.items() if k not in _ASYNCPG_INCOMPATIBLE}
    new_query = urlencode(filtered, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


SQLALCHEMY_DATABASE_URL = _build_asyncpg_url(settings.DATABASE_URL)

engine_kwargs = {
    "echo": False,
}

if "sqlite" not in SQLALCHEMY_DATABASE_URL:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    })

if "neon.tech" in SQLALCHEMY_DATABASE_URL:
    engine_kwargs["connect_args"] = {"ssl": True}

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_kwargs
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
