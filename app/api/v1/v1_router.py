from fastapi import APIRouter

from app.api.v1.endpoints import job_router

router = APIRouter()

router.include_router(job_router.router)
