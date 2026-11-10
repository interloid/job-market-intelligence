from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SourceStatusEnum, pg_enum
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.ingestion_runs_model import IngestionRun
    from app.models.jobs_model import Job


class Source(Base):
    __tablename__ = "sources"

    __table_args__ = (
        CheckConstraint("fetch_interval_minutes > 0", name="fetch_interval_positive"),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    attribution_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    base_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    terms_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    fetch_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[SourceStatusEnum] = mapped_column(
        pg_enum(SourceStatusEnum, name="source_enum"),
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

    request_budget_per_day: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    retention_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    approved_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adapter_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
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

    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun",
        back_populates="source",
    )

    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="source",
    )
