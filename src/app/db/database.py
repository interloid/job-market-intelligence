from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    pool_pre_ping=True,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_size=settings.DB_POOL_SIZE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

sessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with sessionLocal() as db:
        try:
            yield db
            await db.commit()
        except SQLAlchemyTimeoutError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise
