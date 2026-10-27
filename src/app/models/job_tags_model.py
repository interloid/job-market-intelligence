from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobSkillTAGEnum
from app.models.base_model import BaseModel
from app.models.tags_model import Tags

if TYPE_CHECKING:
    from app.models.jobs_model import Jobs


class JobTags(BaseModel):
    __tablename__ = "job_tags"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "tag_id",
            name="uq_job_tags_job_tag",
        ),
    )

    status: Mapped[JobSkillTAGEnum] = mapped_column(
        Enum(
            JobSkillTAGEnum,
            name="job_tag_origin",
            values_callable=lambda job_tag_enum: [tag.value for tag in job_tag_enum],
        ),
        nullable=False,
        default=JobSkillTAGEnum.SOURCE,
        server_default=JobSkillTAGEnum.SOURCE.value,
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

    tags: Mapped["Tags"] = relationship(
        "Tags",
        back_populates="job_tags",
    )

    jobs: Mapped["Jobs"] = relationship(
        "Jobs",
        back_populates="job_tags",
    )
