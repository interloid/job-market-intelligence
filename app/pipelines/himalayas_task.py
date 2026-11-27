import logging
from datetime import UTC, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from prefect import task
from prefect.runtime import task_run
from pydantic import ValidationError

from app.adapters.himalayas.adapter import HimalayasAdapter
from app.adapters.himalayas.schema import HimalayasJobSchema
from app.core.constants import PayPeriodEnum
from app.schemas.job_schema import AdapterJobSchema, JobSchema
from app.utils import clean_job_description, generate_content_hash

logger = logging.getLogger(__name__)


def filter_job_record(
    records: list[dict],
) -> tuple[list[dict], list[dict]]:

    job_records = []
    skipped_records = []

    for record in records:
        if (
            isinstance(record, dict)
            and isinstance(record.get("title"), str)
            and record["title"].strip()
            and isinstance(record.get("link"), str)
            and record["link"].strip()
        ):
            job_records.append(record)
        else:
            skipped_records.append(record)

            logger.warning(
                "Skipping invalid Himalayas RSS item. available_keys=%s",
                list(record.keys()) if isinstance(record, dict) else None,
            )

    return job_records, skipped_records


def validate_job_record(
    records: list[dict],
) -> tuple[list[HimalayasJobSchema], list[dict]]:

    valid_records = []
    invalid_records = []

    for record in records:
        try:
            model_validation = HimalayasJobSchema.model_validate(record)
            valid_records.append(model_validation)

        except ValidationError as exc:
            invalid_records.append(
                {
                    "record": record,
                    "error": str(exc),
                }
            )

            logger.warning(
                "Himalayas job validation failed. title=%s, errors=%s",
                record.get("title"),
                exc.errors(include_input=False),
            )

    return valid_records, invalid_records


def parse_himalayas_date(value: str | int | None) -> datetime | None:
    if value is None:
        return None

    date_value = str(value).strip()

    if not date_value:
        return None

    if date_value.lstrip("-").isdigit():
        try:
            return datetime.fromtimestamp(int(date_value), tz=UTC)
        except (ValueError, OverflowError, OSError):
            return None

    try:
        parsed = parsedate_to_datetime(date_value)
    except (ValueError, TypeError, OverflowError):
        try:
            parsed = datetime.fromisoformat(date_value)
        except (ValueError, TypeError, OverflowError):
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def normalize_job_record(
    record: HimalayasJobSchema,
) -> AdapterJobSchema:

    posted_at = parse_himalayas_date(record.published_at)
    expired_at = parse_himalayas_date(record.expiryDate)

    description = record.content_encoded or record.description or record.excerpt

    guid = record.guid.strip()

    if not guid:
        raise ValueError("Job GUID is missing")

    parsed_guid = urlparse(guid)
    path = parsed_guid.path.rstrip("/")

    external_job_id = path.split("/")[-1] if path else guid

    if not external_job_id:
        raise ValueError(f"Unable to extract external job ID from GUID: {guid}")

    if not record.title or not record.title.strip():
        raise ValueError("Job title is missing")

    pay_period = None

    if record.salaryPeriod:
        try:
            pay_period = PayPeriodEnum(record.salaryPeriod.lower())
        except ValueError:
            pay_period = None

    job = JobSchema(
        external_job_id=external_job_id,
        title=record.title,
        company_name=record.company_name,
        description=(clean_job_description(description) if description else None),
        salary_min=(
            Decimal(str(record.minSalary)) if record.minSalary is not None else None
        ),
        salary_max=(
            Decimal(str(record.maxSalary)) if record.maxSalary is not None else None
        ),
        currency=record.currency,
        pay_period=pay_period,
        source_url=record.link,
        apply_url=record.applicationLink,
        posted_at=posted_at,
        expired_at=expired_at,
    )

    job.content_hash = generate_content_hash(job)

    return AdapterJobSchema(
        job=job,
        source_tags=record.categories or [],
    )


def process_job_records(
    records: list[dict],
) -> tuple[list[AdapterJobSchema], int, int, list[dict], list[dict]]:

    filtered_jobs, skipped_records = filter_job_record(records)

    valid_records, invalid_records = validate_job_record(filtered_jobs)

    normalized_records = []

    for record in valid_records:
        try:
            normalized = normalize_job_record(record)
            normalized_records.append(normalized)

        except Exception as exc:
            logger.exception("Failed to normalize Himalayas job record")
            invalid_records.append(
                {
                    "record": record.model_dump(mode="json"),
                    "error": str(exc),
                }
            )

    logger.info(
        (
            "Himalayas processing completed: "
            "total_records=%s, valid_jobs=%s, "
            "invalid_records=%s, skipped_records=%s"
        ),
        len(records),
        len(normalized_records),
        len(invalid_records),
        len(skipped_records),
    )

    return (
        normalized_records,
        len(records),
        len(normalized_records),
        invalid_records,
        skipped_records,
    )


@task(name="fetch_himalayas_jobs", retries=2, retry_delay_seconds=5)
async def fetch_himalayas_jobs(base_url: str) -> tuple[str, list, str, int, int]:

    xml_data, http_status = await HimalayasAdapter.fetch_rss_feed_records(
        base_url=base_url
    )

    raw_records, last_build_date = HimalayasAdapter.parse_rss_feed_records(xml_data)

    if not last_build_date:
        raise ValueError("Himalayas RSS feed missing lastBuildDate")

    retry_count = task_run.run_count - 1

    return xml_data, raw_records, last_build_date, http_status, retry_count


@task(name="process_himalayas_batch")
async def process_himalayas_batch(job_records: list[dict]) -> dict:

    (
        normalized_jobs,
        total_records,
        valid_records,
        invalid_records,
        skipped_records,
    ) = process_job_records(job_records)

    return {
        "normalized_jobs": normalized_jobs,
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "skipped_records": skipped_records,
    }
