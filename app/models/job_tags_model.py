from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobSkillTagEnum, pg_enum
from app.models.base_model import Base

if TYPE_CHECKING:
    from app.models.jobs_model import Job
    from app.models.tags_model import Tag


class JobTag(Base):
    __tablename__ = "job_tags"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "tag_id",
            name="job_tag",
        ),
    )

    status: Mapped[JobSkillTagEnum] = mapped_column(
        pg_enum(JobSkillTagEnum, name="job_tag_origin"),
        nullable=False,
        default=JobSkillTagEnum.SOURCE,
        server_default=JobSkillTagEnum.SOURCE.value,
        index=True,
    )

    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tag: Mapped["Tag"] = relationship(
        "Tag",
        back_populates="job_tags",
    )

    job: Mapped["Job"] = relationship(
        "Job",
        back_populates="job_tags",
    )
