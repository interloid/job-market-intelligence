import logging
from decimal import Decimal

import httpx
from pydantic import ValidationError

from app.adapters.remoteok.schema import RemoteOKJobSchema
from app.models import Source
from app.schemas.job_schema import (
    AdapterJobSchema,
    JobSchema,
    PayPeriodEnum,
    RemoteScopeEnum,
)
from app.utils import clean_job_description, generate_content_hash

logger = logging.getLogger(__name__)


class RemoteOkAdapter:
    @staticmethod
    def filter_job_record(records: list[dict]) -> tuple[list[dict], list[dict]]:
        job_records = []
        skipped_records = []

        for record in records:
            if "id" in record and "position" in record:
                job_records.append(record)
            else:
                skipped_records.append(record)

                logger.warning(
                    "skipping non-job records from remote ok available keys=%s",
                    list(record.keys()),
                )

        return job_records, skipped_records

    @staticmethod
    def validate_job_record(
        records: list[dict],
    ) -> tuple[list[RemoteOKJobSchema], list[dict]]:

        valid_records = []
        invalid_records = []

        for record in records:
            try:
                model_validation = RemoteOKJobSchema.model_validate(record)
                valid_records.append(model_validation)
            except ValidationError as exc:
                invalid_records.append(
                    {
                        "record": record,
                        "error": str(exc),
                    }
                )
                logger.warning(
                    "RemoteOK job validation failed: job_id=%s, errors=%s",
                    record.get("id"),
                    exc.errors(include_input=False),
                )

        return valid_records, invalid_records

    @staticmethod
    def normalize_job_record(record: RemoteOKJobSchema) -> AdapterJobSchema:

        salary_min = (
            Decimal(str(record.salary_min))
            if record.salary_min is not None and record.salary_min > 0
            else None
        )
        salary_max = (
            Decimal(str(record.salary_max))
            if record.salary_max is not None and record.salary_max > 0
            else None
        )

        salary_present = record.salary_min is not None or record.salary_max is not None

        job = JobSchema(
            external_job_id=record.id,
            title=record.position,
            company_name=record.company,
            description=clean_job_description(record.description),
            location=record.location.strip()
            if record.location and record.location.strip()
            else None,
            source_url=record.url,
            apply_url=record.apply_url or record.url,
            posted_at=record.date,
            salary_min=salary_min,
            salary_max=salary_max,
            remote_scope=RemoteScopeEnum.REMOTE,
            currency="USD" if salary_present else None,
            pay_period=PayPeriodEnum.YEAR if salary_present else None,
        )

        job.content_hash = generate_content_hash(job)

        return AdapterJobSchema(
            job=job,
            source_tags=record.tags,
        )

    @staticmethod
    def process_job_records(
        records: list[dict],
    ) -> tuple[list[AdapterJobSchema], int, int, list[dict], list[dict]]:

        filtered_jobs, skipped_records = RemoteOkAdapter.filter_job_record(records)

        valid_records, invalid_records = RemoteOkAdapter.validate_job_record(
            filtered_jobs
        )

        normalized_records = [
            RemoteOkAdapter.normalize_job_record(record) for record in valid_records
        ]

        logger.info(
            (
                "RemoteOK processing completed: "
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

    @staticmethod
    async def fetch_job_records(source: Source) -> tuple[list[dict], int]:

        try:
            url = source["base_url"]
            headers = {"User-Agent": "AutomatedDataIntelligence/1.0"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=30.0,
                )

                response.raise_for_status()
                http_status = response.status_code

                try:
                    data = response.json()

                except ValueError:
                    logger.exception("RemoteOK API returned invalid JSON")
                    raise

                if not isinstance(data, list):
                    raise TypeError("Expected a list of job records from RemoteOK API")

                if not data:
                    raise ValueError("RemoteOK API returned an empty response")

                if not all(isinstance(record, dict) for record in data):
                    raise ValueError(
                        "RemoteOK API response contains a non-dictionary record"
                    )

                return data, http_status

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning("RemoteOK API returned HTTP status=%s", status_code)
            raise

        except httpx.RequestError as exc:
            logger.warning(
                "RemoteOK API request failed: %s",
                exc,
                exc_info=True,
            )
            raise

    @staticmethod
    async def run(
        source: Source,
    ) -> tuple[list[dict], list[AdapterJobSchema], int, int, list[dict], list[dict]]:
        raw_records, _ = await RemoteOkAdapter.fetch_job_records(source)

        (
            normalized_records,
            total_records,
            valid_records,
            invalid_records,
            skipped_records,
        ) = RemoteOkAdapter.process_job_records(raw_records)

        return (
            raw_records,
            normalized_records,
            total_records,
            valid_records,
            invalid_records,
            skipped_records,
        )
