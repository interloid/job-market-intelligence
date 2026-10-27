from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobSkillTAGEnum
from app.models.base_model import BaseModel
from app.models.skills_model import Skills

if TYPE_CHECKING:
    from app.models.jobs_model import Jobs


class JobSkills(BaseModel):
    __tablename__ = "job_skills"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "skill_id",
            name="uq_job_skills_job_skill",
        ),
    )

    status: Mapped[JobSkillTAGEnum] = mapped_column(
        Enum(
            JobSkillTAGEnum,
            name="job_skill_origin",
            values_callable=lambda job_skill_enum: [
                skill.value for skill in job_skill_enum
            ],
        ),
        nullable=False,
        default=JobSkillTAGEnum.SOURCE,
        server_default=JobSkillTAGEnum.SOURCE.value,
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

    skills: Mapped["Skills"] = relationship(
        "Skills",
        back_populates="job_skills",
    )

    jobs: Mapped["Jobs"] = relationship(
        "Jobs",
        back_populates="job_skills",
    )
