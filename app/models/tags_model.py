from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.job_tags_model import JobTag


class Tag(Base):
    __tablename__ = "tags"

    __table_args__ = (UniqueConstraint("name", name="uq_tags_name"),)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    job_tags: Mapped[list["JobTag"]] = relationship(
        "JobTag",
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
