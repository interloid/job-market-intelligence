from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import IngestionRunStatusEnum
from app.models.ingestion_runs_model import IngestionRun
from app.repositories.base_repo import BaseRepository


class IngestionRunsRepository(BaseRepository[IngestionRun]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=IngestionRun, db=db)

    async def get_by_source_id(self, source_id: UUID) -> list[IngestionRun]:
        stmt = select(IngestionRun).where(IngestionRun.source_id == source_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, ingestion_id: UUID, status: IngestionRunStatusEnum
    ) -> IngestionRun | None:
        ingestion_run = await self.get_by_id(ingestion_id)

        if ingestion_run is None:
            return None

        ingestion_run.status = status
        await self.db.flush()

        return ingestion_run

    async def finish(
        self,
        ingestion_id: UUID,
        status: IngestionRunStatusEnum,
    ) -> IngestionRun | None:
        ingestion_run = await self.get_by_id(ingestion_id)

        if ingestion_run is None:
            return None

        ingestion_run.status = status
        ingestion_run.finished_at = datetime.now(UTC)

        await self.db.flush()
        return ingestion_run

    async def update_counters(
        self,
        ingestion_id: UUID,
        *,
        records_fetched: int,
        records_inserted: int,
        records_updated: int,
        records_skipped: int,
        records_failed: int,
    ) -> IngestionRun | None:
        ingestion_run = await self.get_by_id(ingestion_id)

        if ingestion_run is None:
            return None

        ingestion_run.records_fetched = records_fetched
        ingestion_run.records_inserted = records_inserted
        ingestion_run.records_updated = records_updated
        ingestion_run.records_skipped = records_skipped
        ingestion_run.records_failed = records_failed

        await self.db.flush()
        return ingestion_run
