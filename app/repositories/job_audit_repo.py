from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import JobAuditLogEnum
from app.models.job_audit_logs_model import JobAuditLog
from app.repositories.base_repo import BaseRepository


class JobAuditLogRepository(BaseRepository[JobAuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=JobAuditLog, db=db)

    async def get_by_job_id(self, job_id: UUID) -> list[JobAuditLog]:
        stmt = (
            select(JobAuditLog)
            .where(JobAuditLog.job_id == job_id)
            .order_by(JobAuditLog.changed_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_change_type(
        self, change_type: JobAuditLogEnum
    ) -> list[JobAuditLog]:
        stmt = (
            select(JobAuditLog)
            .where(JobAuditLog.change_type == change_type)
            .order_by(JobAuditLog.changed_at.desc().nulls_last())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[JobAuditLog]:

        stmt = (
            select(JobAuditLog)
            .where(
                JobAuditLog.changed_at >= start_date,
                JobAuditLog.changed_at < end_date,
            )
            .order_by(JobAuditLog.changed_at.desc().nulls_last())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
