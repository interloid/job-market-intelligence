from uuid import UUID
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")
ID = TypeVar("ID", UUID, int, str)


class CursorModel(BaseModel, [T, ID]):
    sort_value: T
    record_id: ID
