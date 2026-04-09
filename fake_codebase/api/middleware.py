"""
Middleware — authentication enforcement, rate limiting, and request logging.
"""

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

RATE_LIMIT_REQUESTS = 100   # max requests per window
RATE_LIMIT_WINDOW = 60      # window size in seconds
PUBLIC_PATHS = {"/auth/login", "/health", "/docs", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiter keyed by client IP address.

    Allows up to RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW seconds per IP.
    Returns HTTP 429 with a Retry-After header when the limit is exceeded.
    """

    def __init__(self, app, requests_per_window: int = RATE_LIMIT_REQUESTS, window_seconds: int = RATE_LIMIT_WINDOW):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._counters: dict = defaultdict(lambda: {"count": 0, "window_start": time.time()})

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercept every request, check rate limit, and either pass through or reject.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler in the chain.

        Returns:
            HTTP 429 response if rate limit exceeded, otherwise the normal response.
        """
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        record = self._counters[client_ip]

        if now - record["window_start"] > self.window_seconds:
            record["count"] = 0
            record["window_start"] = now

        record["count"] += 1

        if record["count"] > self.requests_per_window:
            retry_after = int(self.window_seconds - (now - record["window_start"]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces JWT authentication on all non-public routes.

    Extracts the Bearer token from the Authorization header, validates it,
    and attaches the decoded payload to request.state.user.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate JWT for protected routes and inject user into request state.

        Args:
            request: Incoming HTTP request.
            call_next: Next handler in the middleware chain.

        Returns:
            HTTP 401 if token is missing/invalid on a protected route,
            otherwise the normal response with request.state.user populated.
        """
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or malformed Authorization header."},
            )

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            from auth.authentication import decode_token
            request.state.user = decode_token(token)
        except Exception as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs method, path, status code, and duration for every request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Wrap each request with timing and structured logging.

        Args:
            request: Incoming HTTP request.
            call_next: Next handler.

        Returns:
            The response unchanged — this middleware is purely observational.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
