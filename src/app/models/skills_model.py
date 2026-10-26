from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class Skills(BaseModel):
    __tablename__ = "skills"

    __table_args__ = (UniqueConstraint("name", name="uq_skills_name"),)

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
