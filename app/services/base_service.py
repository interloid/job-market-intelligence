import logging
from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select

logger = logging.getLogger(__name__)


class BaseServices:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def validate_sort_order(sort_order: str):

        normalized_order = sort_order.strip().lower()

        if normalized_order not in {"asc", "desc"}:
            logger.warning(
                "Sort order must be either 'asc' or 'desc' | sort_order=%s", sort_order
            )
            raise BadRequestException(
                message="Sort order must be either 'asc' or 'desc'",
            )
        return normalized_order

    @staticmethod
    def apply_filters(stmt: Select, *, filters: Sequence[Any] | None = None) -> Select:

        if not filters:
            return stmt

        return stmt.where(*filters)

    @staticmethod
    def apply_search(
        stmt: Select,
        *,
        search_expression: Any | None,
    ) -> Select:
        if search_expression is None:
            return stmt

        return stmt.where(search_expression)

    @staticmethod
    def apply_sorting(
        stmt: Select,
        *,
        sort_column: Any,
        sort_order: str,
    ) -> Select:
        if sort_order == "asc":
            return stmt.order_by(sort_column.asc())

        return stmt.order_by(sort_column.desc())
    
    @staticmethod
    def resolve_sort_column(
        *,
        sort_by: str,
        sort_fields: dict[str, Any],
    ):
        sort_column = sort_fields.get(sort_by)

        if sort_column is None:
            raise BadRequestException(
                message=f"Invalid sort field: {sort_by}",
            )

        return sort_column
