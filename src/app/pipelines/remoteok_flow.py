import asyncio

from prefect import flow

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


@flow(name="remoteok_ingestion_flow")
async def remoteok_ingestion_flow():

    source = await fetch_remoteok_source()

    ingestion_run_id = await create_ingestion_run(source_id=source["source_id"])

    current_stage = IngestionErrorStageEnum.FETCH

    try:
        raw_records = await fetch_remoteok_jobs()

        if source["allow_store"]:
            current_stage = IngestionErrorStageEnum.S3_STORAGE

            await store_raw_data_to_s3(
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
        )

        await update_source_run_schedule(source_id=source["source_id"])

    except Exception as exc:
        await fail_ingestion_run(
            ingestion_run_id=ingestion_run_id,
            error_message=str(exc),
            error_stage=current_stage,
        )

        await update_source_run_schedule(source_id=source["source_id"])

        raise


if __name__ == "__main__":
    asyncio.run(remoteok_ingestion_flow())
