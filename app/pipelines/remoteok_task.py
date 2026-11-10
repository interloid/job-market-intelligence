import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from prefect import task
from prefect.runtime import task_run

from app.adapters.remoteok.adapter import RemoteOkAdapter
from app.core.config import get_settings
from app.core.constants import IngestionErrorStageEnum, IngestionRunStatusEnum
from app.db.database import get_session_factory
from app.models import IngestionError, IngestionRun, Source
from app.repositories import (
    IngestionErrorRepository,
    IngestionRunsRepository,
    SourceRepository,
)
from app.schemas.job_schema import AdapterJobSchema
from app.services import JobPersistenceService, S3StorageService

logger = logging.getLogger(__name__)
settings = get_settings()


@task(name="fetch_source_data", retries=2, retry_delay_seconds=5)
async def fetch_remoteok_source(source_id: UUID):

    async with get_session_factory()() as db:
        source_repo = SourceRepository(db)

        source = await source_repo.get_eligible_source(source_id)

        if source is None:
            raise ValueError(
                "RemoteOK source is inactive or not approved for ingestion"
            )

        return {
            "source_id": str(source.id),
            "source_code": source.code,
            "source_name": source.name,
            "base_url": source.base_url,
            "adapter_version": source.adapter_version,
            "allow_store": source.allow_store,
        }


@task(name="update_source_run_schedule")
async def update_source_run_schedule(source_id: str) -> None:

    async with get_session_factory()() as db:
        source_repo = SourceRepository(db)

        try:
            source = await source_repo.update_run_schedule(source_id=UUID(source_id))

            if source is None:
                raise ValueError("Source not found")

            await db.commit()

        except Exception:
            await db.rollback()
            raise


@task(
    name="create_ingestion_run",
    retries=2,
    retry_delay_seconds=5,
)
async def create_ingestion_run(
    source_id: str,
    prefect_flow_id: str,
):

    async with get_session_factory()() as db:
        source_uuid = UUID(source_id)

        ingestion_run_repo = IngestionRunsRepository(db)

        ingestion_run = IngestionRun(
            source_id=source_uuid,
            prefect_flow_id=prefect_flow_id,
            status=IngestionRunStatusEnum.RUNNING,
            started_at=datetime.now(UTC),
        )

        created_run = await ingestion_run_repo.create(ingestion_run)
        await db.commit()

        return str(created_run.id)


@task(
    name="fetch_remoteok_jobs",
    retries=2,
    retry_delay_seconds=5,
)
async def fetch_remoteok_jobs(source: Source) -> tuple[list[dict], int, int]:

    adapter = RemoteOkAdapter()
    raw_records, http_status = await adapter.fetch_job_records(source)
    retry_count = task_run.run_count - 1

    return raw_records, http_status, retry_count


@task(name="process_remoteok_jobs")
async def process_remoteok_jobs(raw_records: list[dict]) -> dict:

    (
        normalized_jobs,
        total_records,
        valid_records,
        invalid_records,
        skipped_records,
    ) = RemoteOkAdapter.process_job_records(raw_records)

    return {
        "normalized_jobs": normalized_jobs,
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "skipped_records": skipped_records,
    }


@task(
    name="store_raw_data_to_s3",
    retries=3,
    retry_delay_seconds=10,
)
async def store_raw_data_to_s3(
    raw_data: Any,
    source_code: str,
    ingestion_run_id: str,
) -> str:

    now = datetime.now(UTC)

    object_key = f"{source_code}/{now:%Y/%m/%d}/{ingestion_run_id}.json"

    storage_service = S3StorageService(
        bucket_name=settings.S3_BUCKET_NAME,
        bucket_region=settings.AWS_REGION,
    )

    uploaded_key = await storage_service.upload_json(
        data=raw_data,
        object_key=object_key,
    )

    return uploaded_key


@task(
    name="persist_normalized_jobs",
    retries=2,
    retry_delay_seconds=5,
)
async def persist_normalized_jobs(
    source_id: str, ingestion_run_id: str, normalized_jobs: list[AdapterJobSchema]
) -> dict:

    created = 0
    updated = 0
    skipped = 0
    failed = 0

    async with get_session_factory()() as db:
        source_uuid = UUID(source_id)
        run_uuid = UUID(ingestion_run_id)

        job_persist = JobPersistenceService(db)

        try:
            for adapter_job in normalized_jobs:
                status, _ = await job_persist.persist_job(
                    source_id=source_uuid,
                    ingestion_run_id=run_uuid,
                    adapter_job=adapter_job,
                )
                if status == "inserted":
                    created += 1

                elif status == "updated":
                    updated += 1

                elif status == "skipped":
                    skipped += 1

            await db.commit()

        except Exception:
            failed += 1
            logger.exception(
                "persist failed external_job_id=%s", adapter_job.job.external_job_id
            )

        return {
            "normalized_jobs": len(normalized_jobs),
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
        }


@task(name="complete_ingestion_run")
async def complete_ingestion_run(
    ingestion_run_id: str,
    records_fetched: int,
    records_inserted: int,
    records_updated: int,
    records_skipped: int,
    records_failed: int,
    s3_path: str | None = None,
    http_status: int | None = None,
    retry_count: int = 0,
):
    async with get_session_factory()() as db:
        run_repo = IngestionRunsRepository(db)

        try:
            ingestion_run = await run_repo.get_by_id(UUID(ingestion_run_id))

            if ingestion_run is None:
                raise ValueError("Ingestion run not found")

            ingestion_run.records_fetched = records_fetched
            ingestion_run.records_inserted = records_inserted
            ingestion_run.records_updated = records_updated
            ingestion_run.records_skipped = records_skipped
            ingestion_run.records_failed = records_failed
            ingestion_run.path = s3_path
            ingestion_run.http_status = http_status
            ingestion_run.retry_count = retry_count

            ingestion_run.status = IngestionRunStatusEnum.SUCCESS
            ingestion_run.finished_at = datetime.now(UTC)

            await db.commit()

        except Exception:
            await db.rollback()
            raise


@task(name="fail_ingestion_run")
async def fail_ingestion_run(
    ingestion_run_id: str,
    error_message: str,
    error_stage: IngestionErrorStageEnum,
):
    async with get_session_factory()() as db:
        run_repo = IngestionRunsRepository(db)
        error_repo = IngestionErrorRepository(db)

        run_uuid = UUID(ingestion_run_id)

        try:
            ingestion_run = await run_repo.get_by_id(run_uuid)

            if ingestion_run is None:
                raise ValueError("Ingestion run not found")

            ingestion_run.status = IngestionRunStatusEnum.FAILED
            ingestion_run.finished_at = datetime.now(UTC)

            error = IngestionError(
                ingestion_run_id=run_uuid,
                error_type="IngestionFailure",
                error_message=error_message,
                error_stage=error_stage,
            )

            await error_repo.create(error)

            await db.commit()

        except Exception:
            await db.rollback()
            raise


@task(name="fetch_due_sources")
async def fetch_due_sources() -> list[dict]:

    async with get_session_factory()() as db:
        source_repo = SourceRepository(db)

        try:
            sources = await source_repo.claim_due_sources()

            claimed_sources = [
                {
                    "source_id": str(source.id),
                    "source_code": source.code,
                }
                for source in sources
            ]

            await db.commit()
            return claimed_sources

        except Exception:
            await db.rollback()
            raise
