from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_job_service
from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)
from app.schemas.job_response_schema import JobResponse
from app.services.job_services import JobServices

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[JobResponse])
async def get_all_jobs(
    search: str | None = Query(default=None, min_length=1),
    source_id: UUID | None = Query(default=None),
    status: JobStatusEnum | None = Query(default=None),
    location: str | None = Query(default=None),
    employment_type: EmploymentTypeEnum | None = Query(default=None),
    remote_scope: RemoteScopeEnum | None = Query(default=None),
    seniority: SeniorityEnum | None = Query(default=None),
    pay_period: PayPeriodEnum | None = Query(default=None),
    min_salary: Decimal | None = Query(default=None, ge=0),
    max_salary: Decimal | None = Query(default=None, ge=0),
    tags: list[str] | None = Query(default=None),
    sort_by: str = Query(
        default="updated_at",
        pattern="^(created_at|updated_at|posted_at|salary_min|salary_max)$",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    job_service: JobServices = Depends(get_job_service),
):
    return await job_service.get_all_jobs(
        search=search,
        source_id=source_id,
        status=status,
        location=location,
        employment_type=employment_type,
        remote_scope=remote_scope,
        seniority=seniority,
        pay_period=pay_period,
        min_salary=min_salary,
        max_salary=max_salary,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order,
    )
