"""Custom ASGI middleware."""
from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to each inbound request for logging correlation."""

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
