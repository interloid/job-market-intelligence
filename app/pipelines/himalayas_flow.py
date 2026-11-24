import logging
from uuid import UUID

from prefect import flow
from prefect.runtime import flow_run

from app.pipelines.remoteok_task import (
    create_ingestion_run,
    persist_normalized_batch,
    complete_ingestion_run,
    fail_ingestion_run,
    update_source_feed_checkpoint,
    update_source_run_schedule,
    fetch_remoteok_source,
    store_raw_data_to_s3
)
from app.pipelines.himalayas_task import process_himalayas_batch
from app.core.constants import IngestionErrorStageEnum
from app.utils.batch import split_into_batches
from app.adapters.himalayas.adapter import HimalayasAdapter

logger = logging.getLogger(__name__)


@flow(name="himalayas_ingestion_flow")
async def himalayas_ingestion_flow(source_id: UUID):

    source = None
    ingestion_run_id = None
    current_stage = IngestionErrorStageEnum.FETCH
    s3_path = None
    prefect_flow_id = str(flow_run.id)
    retry_count = 0

    try:
        source = fetch_remoteok_source()

        ingestion_run_id = await create_ingestion_run(
            source_id=source["source_id"],
            prefect_flow_id=prefect_flow_id,
        )

        xml_data, http_status = await HimalayasAdapter.fetch_rss_feed_records()
        
        if source["allow_store"]:
            current_stage = IngestionErrorStageEnum.S3_STORAGE
                
            s3_path = await store_raw_data_to_s3(
                raw_data=xml_data,
                source_code=source["source_code"],
                ingestion_run_id=ingestion_run_id,
            )
            
        current_stage = IngestionErrorStageEnum.PARSE

        raw_records = HimalayasAdapter.parse_rss_feed_records(xml_data)
            
        job_records = [
            HimalayasAdapter.convert_item_to_dict(item)
            for item in raw_records
        ]
        
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
                    "Processing RemoteOK batch. batch_number=%s, batch_size=%s",
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
            last_updated=last_updated,
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
            "RemoteOK ingestion completed successfully. "
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
                source_id,
                ingestion_run_id,
            )
