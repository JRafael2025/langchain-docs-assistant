"""
Error handlers — custom exceptions and FastAPI error formatting.
"""

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# --- Custom exception hierarchy ---

class AppError(Exception):
    """
    Base class for all application-level errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code string (e.g. 'USER_NOT_FOUND').
        status_code: HTTP status code to return to the client.
    """
    message: str = "An unexpected error occurred."
    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: Optional[str] = None, code: Optional[str] = None):
        self.message = message or self.__class__.message
        self.code = code or self.__class__.code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.code, "message": self.message}


class NotFoundError(AppError):
    """Resource was not found."""
    message = "Resource not found."
    code = "NOT_FOUND"
    status_code = 404


class ConflictError(AppError):
    """Request conflicts with current state (e.g. duplicate email)."""
    message = "Resource already exists."
    code = "CONFLICT"
    status_code = 409


class UnauthorizedError(AppError):
    """Authentication is required or failed."""
    message = "Authentication required."
    code = "UNAUTHORIZED"
    status_code = 401


class ForbiddenError(AppError):
    """Authenticated user lacks permission for this action."""
    message = "You do not have permission to perform this action."
    code = "FORBIDDEN"
    status_code = 403


class BadRequestError(AppError):
    """Request is malformed or contains invalid data."""
    message = "Invalid request data."
    code = "BAD_REQUEST"
    status_code = 400


class ServiceUnavailableError(AppError):
    """A downstream service (DB, payment gateway, etc.) is unavailable."""
    message = "Service temporarily unavailable."
    code = "SERVICE_UNAVAILABLE"
    status_code = 503


# --- FastAPI exception handlers ---

def format_error_response(error_code: str, message: str, status_code: int) -> JSONResponse:
    """
    Build a standardised JSON error response.

    Args:
        error_code: Machine-readable code string.
        message: Human-readable description.
        status_code: HTTP status code.

    Returns:
        JSONResponse with consistent shape: {"error": ..., "message": ...}
    """
    return JSONResponse(
        status_code=status_code,
        content={"error": error_code, "message": message},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handler for all AppError subclasses.

    Logs 5xx errors as ERROR, 4xx as WARNING.
    """
    if exc.status_code >= 500:
        logger.error("AppError [%s] on %s %s: %s", exc.code, request.method, request.url.path, exc.message)
    else:
        logger.warning("AppError [%s] on %s %s: %s", exc.code, request.method, request.url.path, exc.message)

    return format_error_response(exc.code, exc.message, exc.status_code)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.

    Logs the full traceback and returns a generic 500 response so internal
    details are never leaked to clients.

    Args:
        request: The request that triggered the exception.
        exc: The unhandled exception.

    Returns:
        JSON 500 response with generic message.
    """
    logger.error(
        "Unhandled exception on %s %s:\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return format_error_response("INTERNAL_ERROR", "An unexpected error occurred.", 500)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all custom exception handlers on a FastAPI application instance.

    Call this once during app startup:
        register_error_handlers(app)

    Args:
        app: The FastAPI application to register handlers on.
    """
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
