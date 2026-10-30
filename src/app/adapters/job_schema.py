from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)


class JobSchema(BaseModel):
    source_id: UUID | None = None
    external_job_id: str
    title: str
    company_name: str
    description: str | None = None
    location: str | None = None
    remote_scope: RemoteScopeEnum | None = None
    employment_type: EmploymentTypeEnum | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    status: JobStatusEnum | None = None
    content_hash: str | None = None
    country_code: str | None = None
    apply_url: str | None = None
    seniority: SeniorityEnum | None = None
    pay_period: PayPeriodEnum | None = None
    posted_at: datetime | None = None
    verified_at: datetime | None = None
    expired_at: datetime | None = None

    model_config = ConfigDict(extra="ignore")


class AdapterJobSchema(BaseModel):
    job: JobSchema
    source_tag: list[str]
