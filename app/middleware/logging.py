"""Request/response logging middleware with request ID generation."""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.logger import get_logger, set_request_id

logger = get_logger(__name__)

SKIP_LOGGING_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with request ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log incoming request and outgoing response."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Skip logging for health/docs endpoints
        if request.url.path in SKIP_LOGGING_PATHS:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Log incoming request
        start_time = time.time()
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_string": request.url.query,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log outgoing response
        logger.info(
            f"Outgoing response: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
