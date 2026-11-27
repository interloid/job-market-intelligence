import logging
from typing import Any

from prefect import task
from prefect.runtime import task_run

from app.adapters.remoteok.adapter import RemoteOkAdapter
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@task(
    name="fetch_remoteok_jobs",
    retries=2,
    retry_delay_seconds=5,
)
async def fetch_remoteok_jobs(
    source: dict[str, Any],
) -> tuple[list[dict], list[dict], int, int, int]:

    adapter = RemoteOkAdapter()
    (
        raw_records,
        job_records,
        last_updated,
        http_status,
    ) = await adapter.fetch_job_records(source)
    retry_count = task_run.run_count - 1

    return raw_records, job_records, last_updated, http_status, retry_count


@task(name="process_remoteok_batch")
async def process_remoteok_batch(job_records: list[dict]) -> dict:

    (
        normalized_jobs,
        total_records,
        valid_records,
        invalid_records,
        skipped_records,
    ) = RemoteOkAdapter.process_job_records(job_records)

    return {
        "normalized_jobs": normalized_jobs,
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "skipped_records": skipped_records,
    }
