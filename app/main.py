from fastapi import FastAPI

from app.api.api_router import router as api_router
from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.middleware.logging_middleware import LoggingMiddleware
from app.core.logging import setup_logging

setup_logging()

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL if settings.DEBUG else None,
    redoc_url=settings.REDOC_URL if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

app.include_router(api_router)
