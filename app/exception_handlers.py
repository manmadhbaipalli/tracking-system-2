import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.exceptions import AppException
from app.schemas.common import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


def _get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    correlation_id = _get_correlation_id(request)
    logger.warning(
        "AppException: %s [%s]",
        exc.message,
        exc.error_code,
        extra={"correlation_id": correlation_id},
    )
    body = ErrorResponse.create(
        code=exc.error_code,
        message=exc.message,
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = _get_correlation_id(request)
    details = [
        ErrorDetail(field=".".join(str(loc) for loc in err["loc"]), message=err["msg"])
        for err in exc.errors()
    ]
    body = ErrorResponse.create(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        correlation_id=correlation_id,
        details=details,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump())


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = _get_correlation_id(request)
    logger.error(
        "Unhandled exception: %s",
        exc,
        exc_info=True,
        extra={"correlation_id": correlation_id},
    )
    body = ErrorResponse.create(
        code="INTERNAL_ERROR",
        message="An internal server error occurred",
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump())
