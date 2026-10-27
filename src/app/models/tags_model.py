from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.job_tags_model import JobTags


class Tags(BaseModel):
    __tablename__ = "tags"

    __table_args__ = (UniqueConstraint("name", name="uq_tags_name"),)

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    job_tags: Mapped[list["JobTags"]] = relationship(
        "JobTags",
        back_populates="tags",
    )
