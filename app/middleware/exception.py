"""Global exception handler middleware."""

from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.exceptions import AppException
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def exception_middleware(request: Request, call_next):
    """Catch and handle all exceptions.

    Args:
        request: FastAPI request
        call_next: Next middleware/route handler

    Returns:
        Response or error JSON response
    """
    try:
        response = await call_next(request)
        return response
    except AppException as exc:
        request_id = request.state.request_id if hasattr(
            request.state, "request_id"
        ) else "unknown"
        logger.error(
            f"AppException: {exc.message} "
            f"(status: {exc.status_code}, request_id: {request_id})"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "status_code": exc.status_code,
                "request_id": request_id,
            },
        )
    except Exception as exc:
        request_id = request.state.request_id if hasattr(
            request.state, "request_id"
        ) else "unknown"
        logger.error(
            f"Unhandled exception: {str(exc)} "
            f"(request_id: {request_id})",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "status_code": 500,
                "request_id": request_id,
            },
        )
