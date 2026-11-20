from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Literal
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
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
from app.schemas.pagination_schema import CursorModel


class JobRepository(BaseRepository[Job]):
    SORT_FIELDS: ClassVar[dict] = {
        "created_at": Job.created_at,
        "updated_at": Job.updated_at,
        "posted_at": Job.posted_at,
        "salary_min": Job.salary_min,
        "salary_max": Job.salary_max,
    }

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
            escaped_location = self.escape_ilike(location.strip())
            filters.append(
                Job.location.ilike(
                    f"%{escaped_location}%",
                    escape="\\",
                )
            )

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

        normalized_tags = [tag.strip().lower() for tag in tags if tag.strip()]

        if not normalized_tags:
            return stmt

        return stmt.where(
            Job.job_tags.any(JobTag.tag.has(func.lower(Tag.name).in_(normalized_tags)))
        )

    @staticmethod
    def escape_ilike(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def apply_search(
        self,
        stmt: Select,
        *,
        search: str | None = None,
    ) -> Select:

        if not search or not search.strip():
            return stmt

        escaped_search = self.escape_ilike(search.strip())

        search_pattern = f"%{escaped_search}%"

        stmt = stmt.where(
            or_(
                Job.title.ilike(search_pattern, escape="\\"),
                Job.company.ilike(search_pattern, escape="\\"),
                Job.description.ilike(search_pattern, escape="\\"),
            )
        )

        return stmt

    def apply_sorting(
        self,
        stmt: Select,
        *,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        reverse: bool = False,
    ) -> Select:

        sort_column = self.SORT_FIELDS.get(sort_by)

        if sort_column is None:
            raise ValueError(f"Invalid sort field: {sort_by}")

        is_ascending = sort_order == "asc"

        if reverse:
            is_ascending = not is_ascending

        if is_ascending:
            order_column = sort_column.asc()
            id_column = Job.id.asc()
        else:
            order_column = sort_column.desc()
            id_column = Job.id.desc()

        if reverse:
            order_column = (
                sort_column.desc().nulls_first()
                if is_ascending
                else sort_column.asc().nulls_first()
            )
            id_column = Job.id.desc() if is_ascending else Job.id.asc()
        else:
            order_column = order_column.nulls_last()

        stmt = stmt.order_by(order_column, id_column)

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

        stmt = self.build_jobs_query(
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
        cursor: CursorModel | None = None,
        direction: Literal["next", "prev"] = "next",
        reverse: bool = False,
    ) -> Select:

        stmt = self.build_query().options(
            selectinload(Job.job_tags).selectinload(JobTag.tag)
        )

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

        stmt = self.apply_cursor_filter(
            stmt,
            cursor,
            sort_by=sort_by,
            sort_order=sort_order,
            direction=direction,
        )

        stmt = self.apply_sorting(
            stmt,
            sort_by=sort_by,
            sort_order=sort_order,
            reverse=reverse,
        )

        return stmt

    def apply_cursor_filter(
        self,
        stmt: Select,
        cursor: CursorModel | None,
        *,
        sort_by: str,
        sort_order: str,
        direction: Literal["next", "prev"] = "next",
    ) -> Select:

        if cursor is None:
            return stmt

        sort_column = self.SORT_FIELDS[sort_by]

        is_ascending = sort_order == "asc"
        is_next = direction == "next"

        use_greater_than = is_ascending == is_next

        if cursor.sort_value is None:
            id_filter = (
                Job.id > cursor.record_id
                if use_greater_than
                else Job.id < cursor.record_id
            )

            if is_next:
                return stmt.where(
                    and_(
                        sort_column.is_(None),
                        id_filter,
                    )
                )

            return stmt.where(
                or_(
                    sort_column.is_not(None),
                    and_(
                        sort_column.is_(None),
                        id_filter,
                    ),
                )
            )

        comparison = (
            sort_column > cursor.sort_value
            if use_greater_than
            else sort_column < cursor.sort_value
        )

        id_filter = (
            Job.id > cursor.record_id if use_greater_than else Job.id < cursor.record_id
        )

        filters = [
            comparison,
            and_(
                sort_column == cursor.sort_value,
                id_filter,
            ),
        ]

        if is_next:
            filters.append(sort_column.is_(None))

        return stmt.where(or_(*filters))

    async def paginate_jobs(
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
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Job], bool]:

        stmt = self.build_jobs_query(
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
            cursor=cursor,
            direction=direction,
            reverse=(direction == "prev"),
        )

        stmt = stmt.limit(limit + 1)

        result = await self.db.execute(stmt)

        jobs = list(result.scalars().all())

        has_more = len(jobs) > limit

        jobs = jobs[:limit]

        if direction == "prev":
            jobs.reverse()

        return jobs, has_more
