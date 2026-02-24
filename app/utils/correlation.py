"""
Correlation ID middleware for request tracking and audit logging.
"""

import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add correlation ID to request and response."""
        correlation_id = request.headers.get('x-correlation-id')

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store correlation ID in request state
        request.state.correlation_id = correlation_id

        # Call the next middleware/endpoint
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers['x-correlation-id'] = correlation_id

        return response


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state."""
    return getattr(request.state, 'correlation_id', str(uuid.uuid4()))