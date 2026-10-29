from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_tags_model import JobTag
from app.repositories.base_repo import BaseRepository


class JobTagRepository(BaseRepository[JobTag]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=JobTag, db=db)

    async def get_by_job_id(self, job_id: UUID) -> list[JobTag]:
        stmt = select(JobTag).where(JobTag.job_id == job_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_tag_id(self, tag_id: UUID) -> list[JobTag]:
        stmt = select(JobTag).where(JobTag.tag_id == tag_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_job_and_tag(self, job_id: UUID, tag_id: UUID) -> JobTag | None:
        stmt = select(JobTag).where(
            JobTag.job_id == job_id,
            JobTag.tag_id == tag_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
