from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.job_skills_model import JobSkills


class Skills(BaseModel):
    __tablename__ = "skills"

    __table_args__ = (UniqueConstraint("name", name="uq_skills_name"),)

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    job_skills: Mapped[list["JobSkills"]] = relationship(
        "JobSkills",
        back_populates="skills",
    )
