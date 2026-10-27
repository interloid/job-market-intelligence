from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import IngestionErrorStageEnum, pg_enum
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.ingestion_runs_model import IngestionRun


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ingestion_runs.id"),
        nullable=False,
        index=True,
    )

    error_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    error_stage: Mapped[IngestionErrorStageEnum] = mapped_column(
        pg_enum(IngestionErrorStageEnum, name="ingestion_error_enum"),
        nullable=False,
    )

    external_job_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun",
        back_populates="ingestion_errors",
    )
