from fastapi import APIRouter

from app.api.v1.v1_router import router as v1_router
from app.core.config import get_settings

setting = get_settings()

router = APIRouter()

router.include_router(
    v1_router,
    prefix=setting.API_V1_PREFIX,
)
