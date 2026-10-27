from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobStatusEnum
from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.job_audit_logs_model import JobAuditLogs
    from app.models.job_skills_model import JobSkills
    from app.models.job_tags_model import JobTags
    from app.models.source_model import Sources


class Jobs(BaseModel):
    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_jobs_salary_range",
        ),
        UniqueConstraint(
            "source_id",
            "external_job_id",
            name="uq_jobs_source_external_id",
        ),
    )

    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    external_job_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    company_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    remote_scope: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    employee_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    salary_min: Mapped[Decimal | None] = mapped_column(
        Numeric,
        nullable=True,
    )

    salary_max: Mapped[Decimal | None] = mapped_column(
        Numeric,
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    status: Mapped[JobStatusEnum] = mapped_column(
        Enum(
            JobStatusEnum,
            name="job_enum",
            values_callable=lambda job_enum: [job.value for job in job_enum],
        ),
        nullable=False,
        default=JobStatusEnum.ACTIVE,
        server_default=JobStatusEnum.ACTIVE.value,
        index=True,
    )

    content_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    country_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    apply_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    seniority: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    pay_period: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    job_audit_logs: Mapped[list["JobAuditLogs"]] = relationship(
        "JobAuditLogs",
        back_populates="jobs",
    )

    sources: Mapped["Sources"] = relationship(
        "Sources",
        back_populates="jobs",
    )

    job_skills: Mapped[list["JobSkills"]] = relationship(
        "JobSkills",
        back_populates="jobs",
        cascade="all, delete-orphan",
    )

    job_tags: Mapped[list["JobTags"]] = relationship(
        "JobTags",
        back_populates="jobs",
        cascade="all, delete-orphan",
    )
