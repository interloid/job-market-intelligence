import logging

from prefect import task
from pydantic import ValidationError

from app.adapters.himalayas.schema import HimalayasJobSchema
from app.schemas.job_schema import AdapterJobSchema, JobSchema
from app.utils import clean_job_description, generate_content_hash

logger = logging.getLogger(__name__)


@staticmethod
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


from pydantic import ValidationError

@staticmethod
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


@staticmethod
async def normalize_job_record(
    record: HimalayasJobSchema,
) -> AdapterJobSchema:

    description = record.content or record.description

    job = JobSchema(
        external_job_id=record.guid,
        title=record.title,
        company_name=record.company_name,
        description=clean_job_description(description),
        source_url=record.link,
        apply_url=record.link,
        posted_at=record.published_at,
    )

    job.content_hash = generate_content_hash(job)

    return AdapterJobSchema(
        job=job,
        source_tags=record.categories,
    )
    
@staticmethod
def process_job_records(
    records: list[dict],
) -> tuple[list[AdapterJobSchema], int, int, list[dict], list[dict]]:

    filtered_jobs, skipped_records = filter_job_record(records)

    valid_records, invalid_records = validate_job_record(
        filtered_jobs
    )

    normalized_records = [
        normalize_job_record(record)
        for record in valid_records
    ]

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
    ) = process_job_records(job_records)

    return {
        "normalized_jobs": normalized_jobs,
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "skipped_records": skipped_records,
    }
    