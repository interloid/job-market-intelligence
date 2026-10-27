from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global engine, SessionLocal
    if engine is None:
        settings = get_settings()
        engine = create_async_engine(
            settings.DATABASE_URL.get_secret_value(),
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_size=settings.DB_POOL_SIZE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
        SessionLocal = async_sessionmaker(
            bind=engine,
            autoflush=False,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return engine


async def get_db():
    if SessionLocal is None:
        get_engine()
    if SessionLocal is None:
        raise RuntimeError("Database session factory was not initialized")
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise


async def dispose_engine() -> None:
    if engine is not None:
        await engine.dispose()
