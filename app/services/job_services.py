from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)
from app.core.cursor import CursorCode
from app.repositories import JobRepository
from app.schemas import CursorModel, CursorResponse, JobResponse
from app.services.base_service import BaseServices


class JobServices(BaseServices):
    def __init__(self, db: AsyncSession, job: JobRepository):
        super().__init__(db)
        self.job_repo = job

    async def get_all_jobs(
        self,
        *,
        limit: int = 10,
        cursor: CursorModel | None = None,
        direction: Literal["next", "prev"] = "next",
        search: str | None = None,
        source_id: UUID | None = None,
        status: JobStatusEnum | None = None,
        location: str | None = None,
        employment_type: EmploymentTypeEnum | None = None,
        remote_scope: RemoteScopeEnum | None = None,
        seniority: SeniorityEnum | None = None,
        pay_period: PayPeriodEnum | None = None,
        min_salary: Decimal | None = None,
        max_salary: Decimal | None = None,
        tags: list[str] | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> CursorResponse[JobResponse]:

        jobs, has_more = await self.job_repo.paginate_jobs(
            limit=limit,
            cursor=cursor,
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

        if not jobs:
            return CursorResponse(
                data=[],
                next_cursor=None,
                prev_cursor=None,
                has_next=False,
                has_prev=False,
            )

        first_record = jobs[0]
        last_record = jobs[-1]

        if direction == "next":
            has_next = has_more
            has_prev = cursor is not None
        else:
            has_prev = has_more
            has_next = cursor is not None

        next_cursor = None
        prev_cursor = None

        if has_next:
            next_cursor = CursorCode.encode(
                CursorModel(
                    sort_value=getattr(last_record, sort_by),
                    record_id=last_record.id,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
            )

        if has_prev:
            prev_cursor = CursorCode.encode(
                CursorModel(
                    sort_value=getattr(first_record, sort_by),
                    record_id=first_record.id,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
            )

        return CursorResponse(
            data=[JobResponse.model_validate(job) for job in jobs],
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_next,
            has_prev=has_prev,
        )
