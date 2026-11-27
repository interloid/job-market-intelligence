from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class HimalayasJobSchema(BaseModel):
    title: str | None = None
    excerpt: str | None = None

    company_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("companyName", "company_name"),
    )
    companySlug: str | None = None
    companyLogo: str | None = None

    employmentType: str | None = None

    locationRestrictions: list[str] | None = None
    timezoneRestrictions: list[str] | None = None

    categories: list[str] | None = None
    parentCategories: list[str] | None = None

    minSalary: float | None = None
    maxSalary: float | None = None
    salaryPeriod: str | None = None
    currency: str | None = None

    description: str | None = None

    published_at: str | int | None = Field(
        default=None,
        validation_alias=AliasChoices("pubDate", "published_at"),
    )
    expiryDate: str | int | None = None

    applicationLink: str | None = None
    guid: str

    model_config = ConfigDict(extra="ignore")
