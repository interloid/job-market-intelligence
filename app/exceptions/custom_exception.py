from fastapi import status

from app.exceptions.base_exception import AppException


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Bad request",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            details=details,
        )
