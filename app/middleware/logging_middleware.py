import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, and latency for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.info(
            "%(method)s %(path)s -> %(status)s (%(duration).1fms) [%(correlation_id)s]",
            {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration": duration_ms,
                "correlation_id": correlation_id,
            },
        )
        return response
