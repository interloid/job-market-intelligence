import asyncio
import logging
from datetime import UTC
from email.utils import parsedate_to_datetime
from uuid import UUID

from prefect import flow
from prefect.runtime import flow_run

from app.adapters.himalayas.adapter import HimalayasAdapter
from app.core.constants import IngestionErrorStageEnum
from app.pipelines.common_task import (
    complete_ingestion_run,
    create_ingestion_run,
    fail_ingestion_run,
    fetch_source_data,
    persist_normalized_batch,
    store_raw_data_to_s3,
    update_source_feed_checkpoint,
    update_source_run_schedule,
)
from app.pipelines.himalayas_task import fetch_himalayas_jobs, process_himalayas_batch
from app.utils.batch import split_into_batches

logger = logging.getLogger(__name__)


@flow(name="himalayas_ingestion_flow")
async def himalayas_ingestion_flow(source_id: UUID):

    source = None
    ingestion_run_id = None
    current_stage = IngestionErrorStageEnum.FETCH
    s3_path = None
    prefect_flow_id = str(flow_run.id)

    try:
        source = await fetch_source_data(source_id=source_id)

        if source["batch_size"] <= 0:
            raise ValueError("Source batch_size must be greater than zero")

        ingestion_run_id = await create_ingestion_run(
            source_id=source["source_id"],
            prefect_flow_id=prefect_flow_id,
        )

        (
            _xml_data,
            raw_records,
            last_build_date,
            http_status,
            retry_count,
        ) = await fetch_himalayas_jobs(base_url=source["base_url"])

        parsed_build_date = parsedate_to_datetime(last_build_date)

        if parsed_build_date.tzinfo is None:
            parsed_build_date = parsed_build_date.replace(tzinfo=UTC)

        last_build_timestamp = int(parsed_build_date.timestamp())

        job_records = [
            HimalayasAdapter.convert_item_to_dict(item) for item in raw_records
        ]

        previous_updated = source["last_feed_updated"]

        if previous_updated is not None and last_build_timestamp < previous_updated:
            raise ValueError(
                f"Himalayas feed timestamp regressed. "
                f"Previous: {previous_updated}, "
                f"Current: {last_build_timestamp}"
            )

        has_updated = (
            previous_updated is None or last_build_timestamp > previous_updated
        )

        if not has_updated:
            logger.info(
                "No new feed updates. Skipping processing. "
                "source_id=%s, last_updated=%s",
                source["source_id"],
                last_build_date,
            )

            await complete_ingestion_run(
                ingestion_run_id=ingestion_run_id,
                records_fetched=0,
                records_updated=0,
                records_skipped=0,
                records_inserted=0,
                records_failed=0,
                s3_path=None,
                http_status=http_status,
                retry_count=retry_count,
            )

        else:
            if source["allow_store"]:
                current_stage = IngestionErrorStageEnum.S3_STORAGE

                s3_path = await store_raw_data_to_s3(
                    raw_data=job_records,
                    source_code=source["source_code"],
                    ingestion_run_id=ingestion_run_id,
                )

            current_stage = IngestionErrorStageEnum.PARSE

            counters = {
                "total_records": 0,
                "valid_records": 0,
                "invalid_records": 0,
                "skipped_records": 0,
                "created": 0,
                "updated": 0,
                "persisted_skipped": 0,
            }

            for batch_number, job_batch in enumerate(
                split_into_batches(job_records, source["batch_size"]), start=1
            ):
                current_stage = IngestionErrorStageEnum.PARSE

                logger.info(
                    "Processing Himalayas batch. batch_number=%s, batch_size=%s",
                    batch_number,
                    len(job_batch),
                )

                result = await process_himalayas_batch(job_batch)

                current_stage = IngestionErrorStageEnum.PERSIST

                persistence_result = await persist_normalized_batch(
                    source_id=source["source_id"],
                    ingestion_run_id=ingestion_run_id,
                    normalized_jobs=result["normalized_jobs"],
                )

                counters["total_records"] += result["total_records"]
                counters["valid_records"] += result["valid_records"]
                counters["invalid_records"] += len(result["invalid_records"])
                counters["skipped_records"] += len(result["skipped_records"])

                counters["created"] += persistence_result["created"]
                counters["updated"] += persistence_result["updated"]
                counters["persisted_skipped"] += persistence_result["skipped"]

            await update_source_feed_checkpoint(
                source_id=source["source_id"],
                last_updated=last_build_timestamp,
            )

            await complete_ingestion_run(
                ingestion_run_id=ingestion_run_id,
                records_fetched=counters["total_records"],
                records_updated=counters["updated"],
                records_skipped=(
                    counters["skipped_records"] + counters["persisted_skipped"]
                ),
                records_inserted=counters["created"],
                records_failed=counters["invalid_records"],
                s3_path=s3_path,
                http_status=http_status,
                retry_count=retry_count,
            )

            logger.info(
                "Himalayas ingestion completed successfully. "
                "source_id=%s, fetched=%s, inserted=%s, "
                "updated=%s, skipped=%s, failed=%s",
                source["source_id"],
                counters["total_records"],
                counters["created"],
                counters["updated"],
                counters["skipped_records"] + counters["persisted_skipped"],
                counters["invalid_records"],
            )

    except Exception as exc:
        if ingestion_run_id is not None:
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
        if source is not None:
            try:
                await update_source_run_schedule(source_id=source["source_id"])

            except Exception:
                logger.exception(
                    "Failed to update source schedule. source_id=%s, ingestion_run_id=%s",
                    source_id,
                    ingestion_run_id,
                )


if __name__ == "__main__":
    id = UUID("01a212b1-841a-755c-835f-b54d53ccaaae")
    asyncio.run(himalayas_ingestion_flow(source_id=id))
