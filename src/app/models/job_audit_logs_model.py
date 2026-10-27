from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JOBAUDITLOGSENUM
from app.models.base_model import BaseModel
from app.models.ingestion_runs_model import IngestionRuns

if TYPE_CHECKING:
    from app.models.jobs_model import Jobs


class JobAuditLogs(BaseModel):
    __tablename__ = "job_audit_logs"

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    change_type: Mapped[JOBAUDITLOGSENUM] = mapped_column(
        Enum(
            JOBAUDITLOGSENUM,
            name="job_audit_log",
            values_callable=lambda job_audit_log: [
                job_log.value for job_log in job_audit_log
            ],
        ),
        nullable=False,
    )

    changed_fields: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingestion_run: Mapped["IngestionRuns"] = relationship(
        "IngestionRuns",
        back_populates="job_audit_logs",
    )

    jobs: Mapped["Jobs"] = relationship(
        "Jobs",
        back_populates="job_audit_logs",
    )
