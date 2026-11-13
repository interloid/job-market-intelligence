from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories import JobRepository
from app.services.job_services import JobServices


def get_job_service(db: AsyncSession = Depends(get_db)) -> JobServices:

    job_repo = JobRepository(db=db)

    return JobServices(
        db=db,
        job=job_repo,
    )
