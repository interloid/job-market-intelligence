from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_model import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.db = db
        self.model = model

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def list_all(self) -> list[ModelType]:
        stmt = select(self.model)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, record_id: UUID) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == record_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, obj: ModelType) -> ModelType:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.db.delete(obj)
        await self.db.refresh()
