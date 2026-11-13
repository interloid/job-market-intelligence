import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.custom_exception import BadRequestException

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
