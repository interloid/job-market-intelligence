from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import IngestionErrorStatusEnum
from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.ingestion_runs_model import IngestionRuns


class IngestionErrors(BaseModel):
    __tablename__ = "ingestion_errors"

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ingestion_runs.id"),
        nullable=False,
    )

    error_type: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    error_stage: Mapped[IngestionErrorStatusEnum] = mapped_column(
        Enum(
            IngestionErrorStatusEnum,
            name="ingestion_error_enum",
            values_callable=lambda ingestion_error_enum: [
                ingestion_error.value for ingestion_error in ingestion_error_enum
            ],
        ),
        nullable=True,
    )

    external_job_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingestion_run: Mapped["IngestionRuns"] = relationship(
        "IngestionRuns",
        back_populates="ingestion_error",
    )
