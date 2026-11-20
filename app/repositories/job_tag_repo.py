from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from app.core.constants import JobSkillTagEnum
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

    async def create_if_not_exists(self, job_id: UUID, tag_id: UUID) -> JobTag | None:
        stmt = (
            insert(JobTag)
            .values(job_id=job_id, tag_id=tag_id)
            .on_conflict_do_nothing(index_elements=[JobTag.job_id, JobTag.tag_id])
            .returning(JobTag)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_many_if_not_exists(
        self,
        job_id: UUID,
        tag_ids: list[UUID],
    ) -> None:

        if not tag_ids:
            return

        values = [
            {
                "id": uuid7(),
                "job_id": job_id,
                "tag_id": tag_id,
                "status": JobSkillTagEnum.SOURCE,
            }
            for tag_id in set(tag_ids)
        ]

        stmt = (
            insert(JobTag)
            .values(values)
            .on_conflict_do_nothing(index_elements=[JobTag.job_id, JobTag.tag_id])
        )

        await self.db.execute(stmt)

    async def delete_source_tags_not_in(
        self,
        job_id: UUID,
        keep_tag_ids: set[UUID],
    ) -> int:

        stmt = delete(JobTag).where(
            JobTag.job_id == job_id,
            JobTag.status == JobSkillTagEnum.SOURCE,
        )

        if keep_tag_ids:
            stmt = stmt.where(JobTag.tag_id.not_in(keep_tag_ids))

        result = await self.db.execute(stmt)

        return result.rowcount or 0
