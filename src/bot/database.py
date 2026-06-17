from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.bot.config import config
from urllib.parse import urlparse, urlunparse

# Ensure we use asyncpg driver for PostgreSQL
def _ensure_asyncpg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        # Convert to postgresql+asyncpg://
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        # Also handle postgres://
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    # If already has a driver or is another DB, return as is
    return url

database_url = _ensure_asyncpg_url(config.DATABASE_URL)

# Create async engine
engine = create_async_engine(database_url, echo=False)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for declarative models
Base = declarative_base()

# Dependency to get DB session
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session