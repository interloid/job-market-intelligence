from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
    pg_enum,
)
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.job_audit_logs_model import JobAuditLog
    from app.models.job_skills_model import JobSkill
    from app.models.job_tags_model import JobTag
    from app.models.source_model import Source


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="salary_range",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_min >= 0",
            name="salary_min_nonnegative",
        ),
        CheckConstraint(
            "salary_max IS NULL OR salary_max >= 0",
            name="salary_max_nonnegative",
        ),
        UniqueConstraint(
            "source_id",
            "external_job_id",
            name="source_external_id",
        ),
    )

    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    external_job_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    remote_scope: Mapped[RemoteScopeEnum | None] = mapped_column(
        pg_enum(RemoteScopeEnum, name="remote_scope_enum"),
        nullable=True,
    )

    employment_type: Mapped[EmploymentTypeEnum | None] = mapped_column(
        pg_enum(EmploymentTypeEnum, name="employment_type_enum"),
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
        String(3),
        nullable=True,
    )

    status: Mapped[JobStatusEnum] = mapped_column(
        pg_enum(JobStatusEnum, name="job_enum"),
        nullable=False,
        default=JobStatusEnum.ACTIVE,
        server_default=JobStatusEnum.ACTIVE.value,
        index=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    apply_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    seniority: Mapped[SeniorityEnum | None] = mapped_column(
        pg_enum(SeniorityEnum, name="seniority_enum"),
        nullable=True,
    )

    pay_period: Mapped[PayPeriodEnum | None] = mapped_column(
        pg_enum(PayPeriodEnum, name="pay_period_enum"),
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

    expired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    job_audit_logs: Mapped[list["JobAuditLog"]] = relationship(
        "JobAuditLog",
        back_populates="job",
    )

    source: Mapped["Source"] = relationship(
        "Source",
        back_populates="jobs",
    )

    job_skills: Mapped[list["JobSkill"]] = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    job_tags: Mapped[list["JobTag"]] = relationship(
        "JobTag",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
