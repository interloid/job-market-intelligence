from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RemoteOKJobSchema(BaseModel):
    slug: str | None = None
    id: str
    epoch: int | None = None
    date: datetime | None = None
    company: str
    company_logo: str | None = None
    position: str
    tags: list[str]
    description: str | None = None
    location: str | None = None
    apply_url: str | None = None
    original: bool | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    logo: str | None = None
    url: str

    model_config = ConfigDict(extra="ignore")
