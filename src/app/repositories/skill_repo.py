from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skills_model import Skill
from app.repositories.base_repo import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Skill, db=db)

    async def get_by_name(self, name: str) -> Skill | None:
        stmt = select(Skill).where(Skill.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, name: str) -> Skill:

        stmt = (
            insert(Skill)
            .values(name=name)
            .on_conflict_do_nothing(index_elements=[Skill.name])
            .returning(Skill.id)
        )

        result = await self.db.execute(stmt)
        skill_id = result.scalar_one_or_none()

        if skill_id is None:
            skill = await self.get_by_name(name)
            if skill is None:
                raise RuntimeError("Skill could not be retrieved after UPSERT")
            return skill

        skill = await self.get_by_id(skill_id)
        if skill is None:
            raise RuntimeError("Inserted skill could not be retrieved")

        return skill
