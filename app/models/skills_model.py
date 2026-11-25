from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.job_skills_model import JobSkill


class Skill(Base):
    __tablename__ = "skills"

    __table_args__ = (UniqueConstraint("name", name="uq_skills_name"),)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    job_skills: Mapped[list["JobSkill"]] = relationship(
        "JobSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
