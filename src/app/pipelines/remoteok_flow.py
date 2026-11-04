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
)

@flow(name="remoteok_ingestion_flow")
async def remoteok_ingestion_flow():

    source = await fetch_remoteok_source()

    ingestion_run_id = await create_ingestion_run(source_id=source["source_id"])

    current_stage = IngestionErrorStageEnum.FETCH

    try:
        result = await fetch_remoteok_jobs()

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

    except Exception as exc:
        await fail_ingestion_run(
            ingestion_run_id=ingestion_run_id,
            error_message=str(exc),
            error_stage=current_stage,
        )
        raise


if __name__ == "__main__":
    asyncio.run(remoteok_ingestion_flow())

