from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tags_model import Tag
from app.repositories.base_repo import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Tag, db=db)

    async def get_by_name(self, name: str) -> Tag | None:
        stmt = select(Tag).where(Tag.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, name: str) -> Tag:

        stmt = (
            insert(Tag)
            .values(name=name)
            .on_conflict_do_nothing(index_elements=[Tag.name])
            .returning(Tag.id)
        )

        result = await self.db.execute(stmt)
        tag_id = result.scalar_one_or_none()

        if tag_id is None:
            tag = await self.get_by_name(name)
            if tag is None:
                raise RuntimeError("Tag could not be retrieved after UPSERT")
            return tag

        tag = await self.get_by_id(tag_id)
        if tag is None:
            raise RuntimeError("Inserted tag could not be retrieved")

        return tag
