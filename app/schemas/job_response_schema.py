from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    external_job_id: str

    title: str
    company_name: str
    description: str | None
    location: str | None

    remote_scope: RemoteScopeEnum | None
    employment_type: EmploymentTypeEnum | None
    seniority: SeniorityEnum | None

    salary_min: Decimal | None
    salary_max: Decimal | None
    currency: str | None
    pay_period: PayPeriodEnum | None

    status: JobStatusEnum
    country_code: str | None

    source_url: str | None
    apply_url: str | None

    posted_at: datetime | None
    verified_at: datetime | None
    expired_at: datetime | None
    job_tags: list[str] = []

    @field_validator("job_tags", mode="before")
    @classmethod
    def extract_tag_names(cls, value):
        if not value:
            return []

        return [job_tag.tag.name for job_tag in value if job_tag.tag is not None]


class TagResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class JobTagResponse(BaseModel):
    tag: TagResponse

    model_config = ConfigDict(from_attributes=True)
