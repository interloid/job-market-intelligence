from uuid import UUID

from pydantic import BaseModel


class CursorModel[T, ID: (UUID, int, str)](BaseModel):
    sort_value: T
    record_id: ID


class CursorResponse[T](BaseModel):
    data: list[T]
    next_cursor: str | None
    prev_cursor: str | None
    has_next: bool
    has_prev: bool
