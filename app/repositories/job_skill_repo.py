from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_skills_model import JobSkill
from app.repositories.base_repo import BaseRepository


class JobSkillRepository(BaseRepository[JobSkill]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=JobSkill, db=db)

    async def get_by_job_id(self, job_id: UUID) -> list[JobSkill]:
        stmt = select(JobSkill).where(JobSkill.job_id == job_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_skill_id(self, skill_id: UUID) -> list[JobSkill]:
        stmt = select(JobSkill).where(JobSkill.skill_id == skill_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_job_and_skill(
        self, job_id: UUID, skill_id: UUID
    ) -> JobSkill | None:
        stmt = select(JobSkill).where(
            JobSkill.job_id == job_id,
            JobSkill.skill_id == skill_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
