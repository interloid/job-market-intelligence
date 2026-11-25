from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HimalayasJobSchema(BaseModel):
    title: str
    description: str | None = None

    link: str
    guid: str | None = None

    categories: list[str] = Field(default_factory=list)

    published_at: datetime | None = None

    company_name: str | None = None
    company_logo: str | None = None

    location_restrictions: list[str] = Field(default_factory=list)

    timezone_restrictions: list[int] = Field(default_factory=list)

    content: str | None = None
    expiry_date: datetime | None = None

    media_image_url: str | None = None

    model_config = ConfigDict(extra="ignore")
