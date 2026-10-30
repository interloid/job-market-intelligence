from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobAuditLogEnum, pg_enum
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.ingestion_runs_model import IngestionRun
    from app.models.jobs_model import Job


class JobAuditLog(Base):
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

    change_type: Mapped[JobAuditLogEnum] = mapped_column(
        pg_enum(JobAuditLogEnum, name="job_audit_log"),
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

    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun",
        back_populates="job_audit_logs",
    )

    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="job_audit_logs",
    )
