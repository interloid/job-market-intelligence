from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.job_schema import AdapterJobSchema
from app.core.constants import JobAuditLogEnum, JobSkillTagEnum, JobStatusEnum
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

        job_data = adapter_job.job.model_dump(
            exclude={"source_id", "status", "verified_at"}
        )

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

    async def sync_job_tags(
        self,
        job_id: UUID,
        source_tags: list[str],
    ) -> bool:

        incoming_tag_ids = set()

        for tag_name in source_tags:
            normalized_name = tag_name.strip().lower()

            if not normalized_name:
                continue

            tag = await self.tag_repo.get_or_create(normalized_name)
            incoming_tag_ids.add(tag.id)

        existing_job_tags = await self.job_tag_repo.get_by_job_id(job_id)

        existing_source_tags = {
            job_tag.tag_id: job_tag
            for job_tag in existing_job_tags
            if job_tag.status == JobSkillTagEnum.SOURCE
        }

        changed = False

        for tag_id, job_tag in existing_source_tags.items():
            if tag_id not in incoming_tag_ids:
                await self.job_tag_repo.delete(job_tag)
                changed = True

        for tag_id in incoming_tag_ids:
            if tag_id not in existing_source_tags:
                await self.job_tag_repo.create_if_not_exists(
                    job_id=job_id,
                    tag_id=tag_id,
                )
                changed = True

        return changed

    async def persist_job(
        self, source_id: UUID, ingestion_run_id: UUID, adapter_job: AdapterJobSchema
    ) -> tuple[str, Job]:

        existing_job = await self.job_repo.get_by_source_and_external_id(
            source_id=source_id,
            external_job_id=adapter_job.job.external_job_id,
        )

        if existing_job is None:
            job = await self.create_job(
                source_id=source_id,
                ingestion_run_id=ingestion_run_id,
                adapter_job=adapter_job,
            )

            return "inserted", job

        tag_changed = await self.sync_job_tags(
            job_id=existing_job.id, source_tags=adapter_job.source_tags
        )

        incoming_job = adapter_job.job

        if existing_job.content_hash == incoming_job.content_hash:
            existing_job.verified_at = datetime.now(UTC)

            old_status = existing_job.status

            was_inactive = existing_job.status != JobStatusEnum.ACTIVE

            if existing_job.status != JobStatusEnum.ACTIVE:
                existing_job.status = JobStatusEnum.ACTIVE
                existing_job.expired_at = None

            await self.job_repo.update(existing_job)

            if tag_changed or was_inactive:
                if was_inactive:
                    audit_log = JobAuditLog(
                        ingestion_run_id=ingestion_run_id,
                        job_id=existing_job.id,
                        change_type=JobAuditLogEnum.UPDATED,
                        changed_fields={
                            "status": {
                                "old": old_status.value,
                                "new": JobStatusEnum.ACTIVE.value,
                            }
                        },
                        changed_at=datetime.now(UTC),
                    )
                    await self.job_audit_repo.create(audit_log)
                return "updated", existing_job

            return "skipped", existing_job

        update_data = incoming_job.model_dump(
            exclude={
                "source_id",
                "external_job_id",
                "status",
                "verified_at",
                "expired_at",
            }
        )

        audit_data = incoming_job.model_dump(
            mode="json",
            exclude={
                "source_id",
                "external_job_id",
                "status",
                "verified_at",
                "expired_at",
            },
        )

        changed_fields = {}

        for field, new_value in update_data.items():
            old_value = getattr(existing_job, field)

            if old_value != new_value:
                changed_fields[field] = {
                    "old": str(old_value) if old_value is not None else None,
                    "new": audit_data[field],
                }
                setattr(existing_job, field, new_value)

        existing_job.status = JobStatusEnum.ACTIVE
        existing_job.verified_at = datetime.now(UTC)
        existing_job.expired_at = None

        await self.job_repo.update(existing_job)

        if changed_fields:
            audit_log = JobAuditLog(
                ingestion_run_id=ingestion_run_id,
                job_id=existing_job.id,
                change_type=JobAuditLogEnum.UPDATED,
                changed_fields=changed_fields,
                changed_at=datetime.now(UTC),
            )
            await self.job_audit_repo.create(audit_log)

        return "updated", existing_job
