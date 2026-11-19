from contextvars import ContextVar
from datetime import datetime, UTC
from uuid6 import uuid7


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_request_id() -> str:
    return str(uuid7())


request_id_ctx: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)

method_ctx: ContextVar[str] = ContextVar(
    "method",
    default="-",
)

path_ctx: ContextVar[str] = ContextVar(
    "path",
    default="-",
)
