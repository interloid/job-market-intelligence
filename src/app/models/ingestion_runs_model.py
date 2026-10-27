from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import IngestionRunStatusEnum, pg_enum
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.ingestion_errors_model import IngestionError
    from app.models.job_audit_logs_model import JobAuditLog
    from app.models.source_model import Source


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint("records_fetched >= 0", name="records_fetched_nonnegative"),
        CheckConstraint("records_inserted >= 0", name="records_inserted_nonnegative"),
        CheckConstraint("records_updated >= 0", name="records_updated_nonnegative"),
        CheckConstraint("records_skipped >= 0", name="records_skipped_nonnegative"),
        CheckConstraint("records_failed >= 0", name="records_failed_nonnegative"),
        CheckConstraint("retry_count >= 0", name="retry_count_nonnegative"),
    )

    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    prefect_flow_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[IngestionRunStatusEnum] = mapped_column(
        pg_enum(IngestionRunStatusEnum, name="ingestion_enum"),
        nullable=False,
    )

    path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    records_fetched: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        default=0,
        nullable=False,
    )

    records_inserted: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        default=0,
        nullable=False,
    )

    records_updated: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        default=0,
        nullable=False,
    )

    records_skipped: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        default=0,
        nullable=False,
    )

    records_failed: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        default=0,
        nullable=False,
    )

    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    source: Mapped["Source"] = relationship(
        "Source",
        back_populates="ingestion_runs",
    )

    ingestion_errors: Mapped[list["IngestionError"]] = relationship(
        "IngestionError",
        back_populates="ingestion_run",
    )

    job_audit_logs: Mapped[list["JobAuditLog"]] = relationship(
        "JobAuditLog",
        back_populates="ingestion_run",
    )
