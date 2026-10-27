from enum import StrEnum

from sqlalchemy import Enum


class SourceStatusEnum(StrEnum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class JobSkillTagEnum(StrEnum):
    SOURCE = "source"
    DERIVED = "derived"


class IngestionRunStatusEnum(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class IngestionErrorStageEnum(StrEnum):
    FETCH = "fetch"
    PARSE = "parse"
    VALIDATE = "validate"
    PERSIST = "persist"


class JobAuditLogEnum(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    STALE = "stale"
    EXPIRED = "expired"


class JobStatusEnum(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    EXPIRED = "expired"


class RemoteScopeEnum(StrEnum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class EmploymentTypeEnum(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    VOLUNTEER = "volunteer"
    OTHER = "other"


class SeniorityEnum(StrEnum):
    INTERN = "intern"
    ENTRY = "entry"
    ASSOCIATE = "associate"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class PayPeriodEnum(StrEnum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


def pg_enum[EnumType: StrEnum](enum_type: type[EnumType], *, name: str) -> Enum:
    return Enum(
        enum_type,
        name=name,
        values_callable=lambda members: [member.value for member in members],
    )
