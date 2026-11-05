from datetime import UTC, datetime, timedelta
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

    async def update_run_schedule(self, source_id: UUID) -> Source | None:
        source = await self.get_by_id(source_id)

        if source is None:
            return None

        now = datetime.now(UTC)

        source.last_run_at = now
        source.next_run_at = now + timedelta(minutes=source.fetch_interval_minutes)
        await self.db.flush()

        return source

    async def get_eligible_source(self, code: str) -> Source | None:
        stmt = select(Source).where(
            Source.code == code,
            Source.allow_fetch == True,
            Source.allow_store == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def claim_due_sources(self) -> list[Source]:
        now = datetime.now(UTC)

        stmt = (
            select(Source)
            .where(
                Source.status == SourceStatusEnum.ACTIVE,
                Source.allow_fetch.is_(True),
                ((Source.next_run_at <= now) | (Source.next_run_at.is_(None))),
            )
            .order_by(Source.next_run_at.asc().nullsfirst())
            .with_for_update(skip_locked=True)
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())
