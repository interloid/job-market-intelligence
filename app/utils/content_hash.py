import hashlib
import json

from app.schemas.job_schema import JobSchema


def generate_content_hash(job: JobSchema) -> str:
    content = {
        "title": job.title,
        "company_name": job.company_name,
        "description": job.description,
        "location": job.location,
        "remote_scope": job.remote_scope,
        "employment_type": job.employment_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "currency": job.currency,
        "apply_url": job.apply_url,
        "seniority": job.seniority,
        "posted_at": job.posted_at,
        "source_url": job.source_url,
        "country_code": job.country_code,
        "pay_period": job.pay_period,
    }

    serialized_data = json.dumps(
        content,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()
