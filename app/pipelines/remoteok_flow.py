import asyncio
import logging
from uuid import UUID

from prefect import flow
from prefect.runtime import flow_run

from app.core.constants import IngestionErrorStageEnum
from app.pipelines.remoteok_task import (
    complete_ingestion_run,
    create_ingestion_run,
    fail_ingestion_run,
    fetch_remoteok_jobs,
    fetch_remoteok_source,
    persist_normalized_jobs,
    process_remoteok_jobs,
    store_raw_data_to_s3,
    update_source_run_schedule,
)

logger = logging.getLogger(__name__)


@flow(name="remoteok_ingestion_flow")
async def remoteok_ingestion_flow(source_id: UUID):

    prefect_flow_id = str(flow_run.id)

    source = await fetch_remoteok_source(source_id=source_id)

    ingestion_run_id = await create_ingestion_run(
        source_id=source["source_id"],
        prefect_flow_id=prefect_flow_id,
    )

    current_stage = IngestionErrorStageEnum.FETCH
    s3_path = None

    try:
        raw_records, http_status, retry_count = await fetch_remoteok_jobs(source)

        if source["allow_store"]:
            current_stage = IngestionErrorStageEnum.S3_STORAGE

            s3_path = await store_raw_data_to_s3(
                raw_data=raw_records,
                source_code=source["source_code"],
                ingestion_run_id=ingestion_run_id,
            )

        current_stage = IngestionErrorStageEnum.PARSE
        result = await process_remoteok_jobs(raw_records)

        current_stage = IngestionErrorStageEnum.PERSIST

        persistence_result = await persist_normalized_jobs(
            source_id=source["source_id"],
            ingestion_run_id=ingestion_run_id,
            normalized_jobs=result["normalized_jobs"],
        )

        await complete_ingestion_run(
            ingestion_run_id=ingestion_run_id,
            records_fetched=result["total_records"],
            records_updated=persistence_result["updated"],
            records_skipped=len(result["skipped_records"])
            + persistence_result["skipped"],
            records_inserted=persistence_result["created"],
            records_failed=len(result["invalid_records"])
            + persistence_result["failed"],
            s3_path=s3_path,
            http_status=http_status,
            retry_count=retry_count,
        )

    except Exception as exc:
        try:
            await fail_ingestion_run(
                ingestion_run_id=ingestion_run_id,
                error_message=str(exc),
                error_stage=current_stage,
            )
        except Exception:
            logger.exception(
                "Failed to record ingestion failure. ingestion_run_id=%s",
                ingestion_run_id,
            )
        raise

    finally:
        try:
            await update_source_run_schedule(source_id=source["source_id"])

        except Exception:
            logger.exception(
                "Failed to update source schedule. source_id=%s, ingestion_run_id=%s",
                source["source_id"],
                ingestion_run_id,
            )


if __name__ == "__main__":
    id = UUID("01a1a5e6-6279-74fa-8489-0a4d5d7ec749")
    asyncio.run(remoteok_ingestion_flow(source_id=id))
