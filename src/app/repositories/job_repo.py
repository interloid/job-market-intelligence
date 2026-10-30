from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import JobStatusEnum
from app.models.jobs_model import Job
from app.repositories.base_repo import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Job, db=db)

    async def get_by_source_and_external_id(
        self, source_id: UUID, external_job_id: str
    ) -> Job | None:
        stmt = select(Job).where(
            Job.source_id == source_id, Job.external_job_id == external_job_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_jobs_by_source_id(self, source_id: UUID) -> list[Job]:
        stmt = select(Job).where(Job.source_id == source_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_content_hash(
        self, source_id: UUID, content_hash: str
    ) -> Job | None:
        stmt = select(Job).where(
            Job.source_id == source_id, Job.content_hash == content_hash
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, job_id: UUID, status: JobStatusEnum) -> Job | None:
        job = await self.get_by_id(job_id)

        if job is None:
            return None
        job.status = status
        await self.db.flush()
        return job

    async def get_jobs_not_seen_since(
        self, source_id: UUID, cutoff: datetime
    ) -> list[Job]:
        stmt = select(Job).where(
            Job.source_id == source_id,
            Job.status == JobStatusEnum.ACTIVE,
            or_(
                Job.verified_at < cutoff,
                Job.verified_at.is_(None),
            ),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
