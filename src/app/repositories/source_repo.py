from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SourceStatusEnum
from app.models.source_model import Source
from app.repositories.base_repo import BaseRepository


class SourceRepository(BaseRepository[Source]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Source, db=db)

    async def get_by_code(self, code: str) -> Source | None:
        stmt = select(Source).where(Source.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_sources(self) -> list[Source]:
        stmt = select(Source).where(Source.status == SourceStatusEnum.ACTIVE)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_last_run_at(self, source_id: UUID) -> Source | None:
        source = await self.get_by_id(source_id)

        if source is None:
            return None

        source.last_run_at = datetime.now(UTC)
        await self.db.flush()

        return source
