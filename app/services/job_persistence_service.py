from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
from app.schemas.job_schema import AdapterJobSchema


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
    ) -> tuple[bool, dict | None]:

        incoming_tag_ids = set()
        incoming_tag_names = set()

        for tag_name in source_tags:
            normalized_name = tag_name.strip().lower()

            if not normalized_name:
                continue

            tag = await self.tag_repo.get_or_create(normalized_name)

            incoming_tag_ids.add(tag.id)
            incoming_tag_names.add(tag.name)

        existing_job_tags = await self.job_tag_repo.get_by_job_id(job_id)

        existing_source_tags = {
            job_tag.tag_id: job_tag
            for job_tag in existing_job_tags
            if job_tag.status == JobSkillTagEnum.SOURCE
        }

        existing_tags = await self.tag_repo.get_by_ids(
            list(existing_source_tags.keys())
        )

        existing_tag_names = {tag.name for tag in existing_tags}

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

        tag_audit = None

        if changed:
            tag_audit = {
                "old": sorted(existing_tag_names),
                "new": sorted(incoming_tag_names),
            }

        return changed, tag_audit

    async def persist_jobs(
        self,
        source_id: UUID,
        ingestion_run_id: UUID,
        adapter_jobs: list[AdapterJobSchema],
    ) -> dict[str, int]:

        results = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
        }

        if not adapter_jobs:
            return results

        external_job_ids = list({item.job.external_job_id for item in adapter_jobs})

        existing_jobs = await self.job_repo.get_by_external_job_ids(
            source_id=source_id,
            external_job_ids=external_job_ids,
        )

        existing_jobs_map = {job.external_job_id: job for job in existing_jobs}

        for adapter_job in adapter_jobs:
            external_job_id = adapter_job.job.external_job_id

            existing_job = existing_jobs_map.get(external_job_id)

            status, job = await self.persist_job(
                source_id=source_id,
                ingestion_run_id=ingestion_run_id,
                adapter_job=adapter_job,
                existing_job=existing_job,
                lookup_existing=False,
            )

            results[status] += 1

            existing_jobs_map[external_job_id] = job

        return results

    async def persist_job(
        self,
        source_id: UUID,
        ingestion_run_id: UUID,
        adapter_job: AdapterJobSchema,
        existing_job: Job | None = None,
        lookup_existing: bool = True,
    ) -> tuple[str, Job]:

        if existing_job is None and lookup_existing:
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

        tag_changed, tag_audit = await self.sync_job_tags(
            job_id=existing_job.id,
            source_tags=adapter_job.source_tags,
        )

        incoming_job = adapter_job.job

        old_status = existing_job.status
        was_inactive = existing_job.status != JobStatusEnum.ACTIVE

        if existing_job.content_hash == incoming_job.content_hash:
            existing_job.verified_at = datetime.now(UTC)

            if was_inactive:
                existing_job.status = JobStatusEnum.ACTIVE
                existing_job.expired_at = None

            await self.job_repo.update(existing_job)

            if tag_changed or was_inactive:
                changed_fields = {}

                if tag_audit:
                    changed_fields["tags"] = tag_audit

                if was_inactive:
                    changed_fields["status"] = {
                        "old": old_status.value,
                        "new": JobStatusEnum.ACTIVE.value,
                    }

                audit_log = JobAuditLog(
                    ingestion_run_id=ingestion_run_id,
                    job_id=existing_job.id,
                    change_type=JobAuditLogEnum.UPDATED,
                    changed_fields=changed_fields,
                    changed_at=datetime.now(UTC),
                )

                await self.job_audit_repo.create(audit_log)

                return "updated", existing_job

            return "skipped", existing_job

        update_data = incoming_job.model_dump(
            exclude={
                "source_id",
                "external_job_id",
                "content_hash",
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
                "content_hash",
                "status",
                "verified_at",
                "expired_at",
            },
        )

        changed_fields = {}

        for field_name, new_value in update_data.items():
            old_value = getattr(existing_job, field_name)

            if old_value != new_value:
                changed_fields[field_name] = {
                    "old": old_value,
                    "new": audit_data[field_name],
                }

                setattr(existing_job, field_name, new_value)

        existing_job.status = JobStatusEnum.ACTIVE
        existing_job.verified_at = datetime.now(UTC)
        existing_job.expired_at = None

        if incoming_job.content_hash is None:
            raise ValueError("Job content_hash cannot be None")

        existing_job.content_hash = incoming_job.content_hash

        if tag_audit:
            changed_fields["tags"] = tag_audit

        if was_inactive:
            changed_fields["status"] = {
                "old": old_status.value,
                "new": JobStatusEnum.ACTIVE.value,
            }

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
