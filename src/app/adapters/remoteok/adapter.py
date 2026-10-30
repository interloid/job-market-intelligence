from decimal import Decimal

from pydantic import ValidationError

from app.adapters.job_schema import AdapterJobSchema, JobSchema
from app.adapters.remoteok.schema import RemoteOKJobSchema


class RemoteOkAdapter:
    @staticmethod
    def filter_job_record(records: list[dict]) -> list[dict]:
        job_records = []

        for record in records:
            if "id" in record and "title" in record and "company in record":
                job_records.append(record)

        return job_records

    @staticmethod
    def validate_job_record(
        records: list[dict],
    ) -> tuple[list[RemoteOKJobSchema], list[dict]]:

        try:
            valid_records = []
            invalid_records = []

            for record in records:
                model_validation = RemoteOKJobSchema.model_validate(record)
                valid_records.append(model_validation)
        except ValidationError as exc:
            invalid_records.append(
                {
                    "record": record,
                    "error": str(exc),
                }
            )

        return valid_records, invalid_records

    @staticmethod
    def normalize_job_record(record: RemoteOKJobSchema) -> AdapterJobSchema:

        job = JobSchema(
            external_job_id=record.id,
            title=record.position,
            company_name=record.company,
            description=record.description,
            location=record.location,
            apply_url=record.apply_url,
            posted_at=record.date,
            salary_min=(
                Decimal(str(record.salary_min)) if record.salary_min else None,
            ),
            salary_max=(
                Decimal(str(record.salary_max)) if record.salary_max else None,
            ),
        )
        return AdapterJobSchema(
            job=job,
            source_tag=record.tag,
        )
