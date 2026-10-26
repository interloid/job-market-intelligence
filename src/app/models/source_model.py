from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SourceStatusEnum
from app.models.base_model import BaseModel
from app.models.ingestion_runs_model import IngestionRuns

if TYPE_CHECKING:
    from app.models.jobs_model import Jobs


class Sources(BaseModel):
    __tablename__ = "sources"

    __table_args__ = (
        CheckConstraint(
            "fetch_interval_minutes > 0", name="ck_sources_fetch_interval_positive"
        ),
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    attribution_text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    base_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    terms_url: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    fetch_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[SourceStatusEnum] = mapped_column(
        Enum(
            SourceStatusEnum,
            name="source_enum",
            values_callable=lambda source_enum: [
                source.value for source in source_enum
            ],
        ),
        nullable=False,
        default=SourceStatusEnum.ACTIVE,
        server_default=SourceStatusEnum.ACTIVE.value,
        index=True,
    )

    allow_fetch: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        default=False,
        nullable=False,
    )

    allow_store: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        default=False,
        nullable=False,
    )

    allow_display: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        default=False,
        nullable=False,
    )

    allow_history: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        default=False,
        nullable=False,
    )

    allow_export: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        default=False,
        nullable=False,
    )

    request_budget_per_day: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
    )

    retention_days: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
    )

    approved_by: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    adapter_version: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    code: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    terms_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingestion_runs: Mapped[list["IngestionRuns"]] = relationship(
        "IngestionRuns",
        back_populates="sources",
    )

    jobs: Mapped[list["Jobs"]] = relationship(
        "Jobs",
        back_populates="sources",
    )
