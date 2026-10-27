from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobSkillTagEnum, pg_enum
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.jobs_model import Job
    from app.models.skills_model import Skill


class JobSkill(Base):
    __tablename__ = "job_skills"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "skill_id",
            name="uq_job_skills_job_skill",
        ),
    )

    status: Mapped[JobSkillTagEnum] = mapped_column(
        pg_enum(JobSkillTagEnum, name="job_skill_origin"),
        nullable=False,
        default=JobSkillTagEnum.SOURCE,
        server_default=JobSkillTagEnum.SOURCE.value,
        index=True,
    )

    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="job_skills",
    )

    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="job_skills",
    )
