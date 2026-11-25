from fastapi import FastAPI

from app.api.api_router import router as api_router
from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.exceptions.handler import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware

setup_logging()

settings = get_settings()

enable_docs = settings.APP_ENV.lower() != "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL if enable_docs else None,
    redoc_url=settings.REDOC_URL if enable_docs else None,
    openapi_url="/openapi.json" if enable_docs else None,
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)

app.include_router(api_router)
