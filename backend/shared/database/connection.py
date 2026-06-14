import os
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import redis.asyncio as aioredis

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://railnerv:railnerv@localhost:5432/railnerv"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

redis_pool = None

async def get_redis():
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_pool

async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        redis_pool = None
