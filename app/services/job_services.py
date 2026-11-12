import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import JobRepository, JobTagRepository

logger = logging.getLogger(__name__)


class JobServices:
    def __init__(self, db: AsyncSession, jobtag: JobTagRepository, job: JobRepository):
        self.db = db
        self.job_repo = job
        self.job_tag = jobtag

    async def get_jobs(
        self,
        *,
        search: str,
    ):

        jobs = await self.job_repo.list_all()

        return jobs
