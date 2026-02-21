"""Request/response logging middleware."""

import uuid
import time
from fastapi import Request
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def logging_middleware(request: Request, call_next):
    """Log request and response details.

    Args:
        request: FastAPI request
        call_next: Next middleware/route handler

    Returns:
        Response from the route handler
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"query_params={dict(request.query_params)}"
    )

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"[{request_id}] Response status {response.status_code} "
        f"duration {duration:.2f}s"
    )

    return response
