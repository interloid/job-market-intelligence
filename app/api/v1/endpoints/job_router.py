from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_job_service
from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)
from app.core.cursor import CursorCode
from app.schemas import CursorModel, CursorResponse, JobResponse
from app.services.job_services import JobServices

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

CURSOR_SCHEMAS = {
    "created_at": CursorModel[datetime, UUID],
    "updated_at": CursorModel[datetime, UUID],
    "posted_at": CursorModel[datetime, UUID],
    "salary_min": CursorModel[Decimal, UUID],
    "salary_max": CursorModel[Decimal, UUID],
}


@router.get(
    "/",
    response_model=CursorResponse[JobResponse],
)
async def get_all_jobs(
    service: Annotated[JobServices, Depends(get_job_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    cursor: Annotated[str | None, Query()] = None,
    direction: Literal["next", "prev"] = Query(default="next"),
    sort_by: Literal[
        "created_at",
        "updated_at",
        "posted_at",
        "salary_min",
        "salary_max",
    ] = "updated_at",
    sort_order: Literal["asc", "desc"] = "desc",
    search: Annotated[str | None, Query(min_length=1)] = None,
    source_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[JobStatusEnum | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    employment_type: Annotated[EmploymentTypeEnum | None, Query()] = None,
    remote_scope: Annotated[RemoteScopeEnum | None, Query()] = None,
    seniority: Annotated[SeniorityEnum | None, Query()] = None,
    pay_period: Annotated[PayPeriodEnum | None, Query()] = None,
    min_salary: Annotated[Decimal | None, Query(ge=0)] = None,
    max_salary: Annotated[Decimal | None, Query(ge=0)] = None,
    tags: Annotated[list[str] | None, Query()] = None,
):
    decoded_cursor = None

    if cursor:
        try:
            cursor_schema = CURSOR_SCHEMAS[sort_by]

            decoded_cursor = CursorCode.decode(
                cursor,
                cursor_schema,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid pagination cursor",
            ) from exc

    return await service.get_all_jobs(
        limit=limit,
        cursor=decoded_cursor,
        direction=direction,
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
