from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import IngestionRunStatusEnum
from app.models.base_model import BaseModel
from app.models.ingestion_errors_model import IngestionErrors


if TYPE_CHECKING:
    from app.models.source_model import Sources
    from app.models.job_audit_logs_model import JobAuditLogs


class IngestionRuns(BaseModel):
    __tablename__ = "ingestion_runs"

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
        Enum(
            IngestionRunStatusEnum,
            name="ingestion_enum",
            values_callable=lambda ingestion_enum: [
                ingestion.value for ingestion in ingestion_enum
            ],
        ),
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

    sources: Mapped["Sources"] = relationship(
        "Sources",
        back_populates="ingestion_runs",
    )

    ingestion_error: Mapped[list["IngestionErrors"]] = relationship(
        "IngestionErrors",
        back_populates="ingestion_run",
    )

    job_audit_logs: Mapped[list["JobAuditLogs"]] = relationship(
        "JobAuditLogs",
        back_populates="ingestion_run",
    )
