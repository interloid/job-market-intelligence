from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)
from app.exceptions.custom_exception import BadRequestException
from app.models.jobs_model import Job
from app.repositories import JobRepository
from app.services.base_service import BaseServices


class JobServices(BaseServices):
    def __init__(self, db: AsyncSession, job: JobRepository):
        super().__init__(db)
        self.job_repo = job

    async def get_all_jobs(
        self,
        *,
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
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Job]:

        normalized_search = search.strip() if search else None

        normalized_sort_order = self.validate_sort_order(sort_order)

        if sort_by not in self.job_repo.SORT_FIELDS:
            raise BadRequestException(message=f"Invalid sort field: {sort_by}")

        if (
            min_salary is not None
            and max_salary is not None
            and min_salary > max_salary
        ):
            raise BadRequestException(
                message="Minimum salary cannot exceed maximum salary"
            )

        normalized_tags = None

        if tags:
            normalized_tags = list(
                dict.fromkeys(tag.strip().lower() for tag in tags if tag)
            )

            if not normalized_tags:
                normalized_tags = None

        return await self.job_repo.get_all_jobs(
            search=normalized_search,
            source_id=source_id,
            status=status,
            location=location,
            employment_type=employment_type,
            remote_scope=remote_scope,
            seniority=seniority,
            pay_period=pay_period,
            min_salary=min_salary,
            max_salary=max_salary,
            tags=normalized_tags,
            sort_by=sort_by,
            sort_order=normalized_sort_order,
        )
