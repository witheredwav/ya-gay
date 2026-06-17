from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.bot.config import config

# Create async engine
engine = create_async_engine(config.DATABASE_URL, echo=False)

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