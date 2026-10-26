from enum import StrEnum


class SourceStatusEnum(StrEnum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class JobSkillTAGEnum(StrEnum):
    SOURCE = "source"
    DERIVED = "derived"


class IngestionRunStatusEnum(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial success"
    FAILED = "failed"


class IngestionErrorStatusEnum(StrEnum):
    FETCH = "fetch"
    PARSE = "parse"
    VALIDATE = "validate"
    PERSIST = "persist"


class JOBAUDITLOGSENUM(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    STALED = "staled"
    EXPIRED = "expired"


class JobStatusEnum(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    CLOSED = "closed"
