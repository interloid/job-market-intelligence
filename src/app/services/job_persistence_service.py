from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.job_schema import AdapterJobSchema
from app.core.constants import JobAuditLogEnum, JobStatusEnum
from app.models import (
    Job,
    JobAuditLog,
)
from app.repositories import (
    JobAuditLogRepository,
    JobRepository,
    JobTagRepository,
    TagRepository,
)


class JobPersistenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = JobRepository(db)
        self.tag_repo = TagRepository(db)
        self.job_audit_repo = JobAuditLogRepository(db)
        self.job_tag_repo = JobTagRepository(db)

    async def create_job(
        self, source_id: UUID, ingestion_run_id: UUID, adapter_job: AdapterJobSchema
    ) -> Job:

        job_data = adapter_job.job.model_dump(exclude={"source_id"})

        job = Job(
            **job_data,
            source_id=source_id,
            status=JobStatusEnum.ACTIVE,
            verified_at=datetime.now(UTC),
        )

        await self.job_repo.create(job)

        await self.create_job_tags(job.id, adapter_job.source_tags)

        audit_log = JobAuditLog(
            ingestion_run_id=ingestion_run_id,
            job_id=job.id,
            change_type=JobAuditLogEnum.CREATED,
            changed_fields={
                field: {"old": None, "new": getattr(job, field)}
                for field in ("title", "company_name", "location")
            },
            changed_at=datetime.now(UTC),
        )

        await self.job_audit_repo.create(audit_log)

        return job

    async def create_job_tags(self, job_id: UUID, source_tags: list[str]) -> None:

        for tag_name in source_tags:
            normalized_name = tag_name.strip().lower()

            if not normalized_name:
                continue

            tag = await self.tag_repo.get_or_create(normalized_name)

            await self.job_tag_repo.create_if_not_exists(
                job_id=job_id,
                tag_id=tag.id,
            )

    async def persist_job(
        self, source_id: UUID, ingestion_run_id: UUID, adapter_job: AdapterJobSchema
    ) -> tuple[str, Job]:

        existing_job = await self.job_repo.get_by_source_and_external_id(
            source_id=source_id,
            external_job_id=adapter_job.external_job_id,
        )

        if existing_job is None:
            job = await self.create_job(
                source_id=source_id,
                ingestion_run_id=ingestion_run_id,
                adapter_job=adapter_job,
            )

            return "inserted", job

        incoming_job = adapter_job.job

        if existing_job.content_hash == incoming_job.content_hash:
            existing_job.verified_at = datetime.now(UTC)

            await self.job_repo.update(existing_job)

            return "skipped", existing_job

        return "existing", existing_job
