import logging
from datetime import UTC, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from prefect import task
from pydantic import ValidationError

from app.adapters.himalayas.schema import HimalayasJobSchema
from app.core.constants import PayPeriodEnum
from app.schemas.job_schema import AdapterJobSchema, JobSchema
from app.utils import clean_job_description, generate_content_hash

logger = logging.getLogger(__name__)


async def filter_job_record(
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


async def validate_job_record(
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

    if isinstance(value, int) or str(value).isdigit():
        return datetime.fromtimestamp(int(value), tz=UTC)

    try:
        parsed = parsedate_to_datetime(str(value))
    except (ValueError, TypeError):
        parsed = datetime.fromisoformat(str(value))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def normalize_job_record(
    record: HimalayasJobSchema,
) -> AdapterJobSchema:

    posted_at = parse_himalayas_date(record.published_at)
    expired_at = parse_himalayas_date(record.expiryDate)

    description = record.description or record.excerpt

    guid = record.guid

    path = urlparse(guid).path.rstrip("/")
    external_job_id = path.split("/")[-1]

    if not record.title:
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
        source_url=record.applicationLink,
        apply_url=record.applicationLink,
        posted_at=posted_at,
        expired_at=expired_at,
    )

    job.content_hash = generate_content_hash(job)

    return AdapterJobSchema(
        job=job,
        source_tags=record.categories or [],
    )


async def process_job_records(
    records: list[dict],
) -> tuple[list[AdapterJobSchema], int, int, list[dict], list[dict]]:

    filtered_jobs, skipped_records = await filter_job_record(records)

    valid_records, invalid_records = await validate_job_record(filtered_jobs)

    normalized_records = [normalize_job_record(record) for record in valid_records]

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


@task(name="process_himalayas_batch")
async def process_himalayas_batch(job_records: list[dict]) -> dict:

    (
        normalized_jobs,
        total_records,
        valid_records,
        invalid_records,
        skipped_records,
    ) = await process_job_records(job_records)

    return {
        "normalized_jobs": normalized_jobs,
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "skipped_records": skipped_records,
    }
