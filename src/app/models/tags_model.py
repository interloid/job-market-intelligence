from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class Tags(BaseModel):
    __tablename__ = "tags"

    __table_args__ = (UniqueConstraint("name", name="uq_tags_name"),)

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
