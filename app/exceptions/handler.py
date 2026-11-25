from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from app.exceptions.base_exception import AppException


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


def register_exception_handlers(app: FastAPI):

    app.add_exception_handler(
        AppException,
        cast(ExceptionHandler, app_exception_handler),
    )
