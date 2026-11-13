from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import (
    EmploymentTypeEnum,
    JobStatusEnum,
    PayPeriodEnum,
    RemoteScopeEnum,
    SeniorityEnum,
)
from app.models import Job, JobTag, Tag
from app.repositories.base_repo import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=Job, db=db)

    async def get_by_source_and_external_id(
        self, source_id: UUID, external_job_id: str
    ) -> Job | None:
        stmt = select(Job).where(
            Job.source_id == source_id,
            Job.external_job_id == external_job_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_job_ids(
        self,
        source_id: UUID,
        external_job_ids: list[str],
    ) -> list[Job]:
        stmt = select(Job).where(
            Job.source_id == source_id,
            Job.external_job_id.in_(external_job_ids),
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_jobs_by_source_id(self, source_id: UUID) -> list[Job]:
        stmt = select(Job).where(Job.source_id == source_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_content_hash(
        self, source_id: UUID, content_hash: str
    ) -> Job | None:
        stmt = select(Job).where(
            Job.source_id == source_id, Job.content_hash == content_hash
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, job_id: UUID, status: JobStatusEnum) -> Job | None:
        job = await self.get_by_id(job_id)

        if job is None:
            return None
        job.status = status
        await self.db.flush()
        return job

    async def get_jobs_not_seen_since(
        self, source_id: UUID, cutoff: datetime
    ) -> list[Job]:
        stmt = select(Job).where(
            Job.source_id == source_id,
            Job.status == JobStatusEnum.ACTIVE,
            or_(
                Job.verified_at < cutoff,
                Job.verified_at.is_(None),
            ),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    SORT_FIELDS = {
        "created_at": Job.created_at,
        "updated_at": Job.updated_at,
        "posted_at": Job.posted_at,
        "salary_min": Job.salary_min,
        "salary_max": Job.salary_max,
    }

    def apply_filters(
        self,
        stmt: Select,
        *,
        source_id: UUID | None = None,
        status: JobStatusEnum | None = None,
        location: str | None = None,
        employment_type: EmploymentTypeEnum | None = None,
        remote_scope: RemoteScopeEnum | None = None,
        seniority: SeniorityEnum | None = None,
        pay_period: PayPeriodEnum | None = None,
        min_salary: Decimal | None = None,
        max_salary: Decimal | None = None,
    ) -> Select:

        filters = []

        if source_id is not None:
            filters.append(Job.source_id == source_id)

        if status is not None:
            filters.append(Job.status == status)

        if location:
            filters.append(Job.location.ilike(f"%{location.strip()}%"))

        if employment_type is not None:
            filters.append(Job.employment_type == employment_type)

        if remote_scope is not None:
            filters.append(Job.remote_scope == remote_scope)

        if seniority is not None:
            filters.append(Job.seniority == seniority)

        if pay_period is not None:
            filters.append(Job.pay_period == pay_period)

        if min_salary is not None:
            filters.append(Job.salary_max >= min_salary)

        if max_salary is not None:
            filters.append(Job.salary_min <= max_salary)

        if filters:
            stmt = stmt.where(*filters)

        return stmt

    def apply_tag_filters(
        self,
        stmt: Select,
        tags: list[str] | None = None,
    ) -> Select:

        if not tags:
            return stmt

        return stmt.where(
            Job.job_tags.any(JobTag.tag.has(func.lower(Tag.name).in_(tags)))
        )

    def apply_search(
        self,
        stmt: Select,
        *,
        search: str | None = None,
    ) -> Select:

        if not search or not search.strip():
            return stmt

        search_pattern = f"%{search.strip()}%"

        search_expression = or_(
            Job.title.ilike(search_pattern),
            Job.company_name.ilike(search_pattern),
            Job.description.ilike(search_pattern),
        )

        return stmt.where(search_expression)

    def apply_sorting(
        self,
        stmt: Select,
        *,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Select:

        sort_column = self.SORT_FIELDS.get(sort_by)

        if sort_column is None:
            raise ValueError(f"Invalid sort field: {sort_by}")

        if sort_order == "asc":
            stmt = stmt.order_by(sort_column.asc(), Job.id.asc())
        else:
            stmt = stmt.order_by(sort_column.desc(), Job.id.desc())

        return stmt

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

        stmt = self.build_query().options(
            selectinload(Job.job_tags).selectinload(JobTag.tag)
        )

        stmt = self.apply_search(stmt, search=search)

        stmt = self.apply_filters(
            stmt,
            source_id=source_id,
            status=status,
            location=location,
            employment_type=employment_type,
            remote_scope=remote_scope,
            seniority=seniority,
            pay_period=pay_period,
            min_salary=min_salary,
            max_salary=max_salary,
        )

        stmt = self.apply_tag_filters(stmt, tags=tags)

        stmt = self.apply_sorting(
            stmt,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    def build_jobs_query(
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
    ) -> Select:

        stmt = self.build_query()

        stmt = self.apply_filters(
            stmt,
            source_id=source_id,
            status=status,
            location=location,
            employment_type=employment_type,
            remote_scope=remote_scope,
            seniority=seniority,
            pay_period=pay_period,
            min_salary=min_salary,
            max_salary=max_salary,
        )

        stmt = self.apply_search(stmt, search=search)

        stmt = self.apply_tag_filters(stmt, tags=tags)

        stmt = self.apply_sorting(
            stmt,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return stmt
