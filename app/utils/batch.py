from collections.abc import Iterator
from typing import TypeVar

T = TypeVar("T")


def split_into_batches(
    records: list[T],
    batch_size: int,
) -> Iterator[list[T]]:
    if batch_size <= 0:
        raise ValueError("Batch size must be greater than 0")

    for index in range(0, len(records), batch_size):
        yield records[index : index + batch_size]
