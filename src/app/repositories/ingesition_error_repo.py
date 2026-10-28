from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_errors_model import IngestionError
from app.repositories.base_repo import BaseRepository


class IngestionErrorRepository(BaseRepository[IngestionError]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=IngestionError, db=db)

    async def get_by_source_id(self, source_id: UUID) -> list[IngestionError]:
        stmt = select(IngestionError).where(IngestionError.source_id == source_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ingestion_run_id(
        self, ingestion_run_id: UUID
    ) -> list[IngestionError]:
        stmt = select(IngestionError).where(
            IngestionError.ingestion_run_id == ingestion_run_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_errors_by_type(self, error_type: str) -> list[IngestionError]:
        stmt = select(IngestionError).where(IngestionError.error_type == error_type)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
