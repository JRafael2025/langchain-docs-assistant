"""
API routes — FastAPI router definitions for auth, orders, and payments.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from auth.authentication import AuthenticationError, TokenExpiredError, login, decode_token
from auth.permissions import PermissionDeniedError, require_role
from payments.processor import PaymentError, process_payment, process_refund

router = APIRouter()


# --- Pydantic schemas ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "USD"
    payment_method_id: str
    metadata: Optional[Dict[str, Any]] = None


class RefundRequest(BaseModel):
    transaction_id: str
    amount: Optional[float] = None


class CreateOrderRequest(BaseModel):
    items: List[Dict[str, Any]]
    currency: str = "USD"


# --- Dependencies ---

def get_current_user(token: str) -> dict:
    """
    FastAPI dependency — decode the Bearer token and return the user payload.

    Args:
        token: JWT token string extracted from the Authorization header.

    Returns:
        Decoded token payload dict with user_id, email, roles.

    Raises:
        HTTPException 401: If token is missing, expired, or invalid.
    """
    try:
        return decode_token(token)
    except TokenExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# --- Auth routes ---

@router.post("/auth/login", tags=["auth"])
def login_endpoint(body: LoginRequest) -> dict:
    """
    Authenticate a user and return JWT tokens.

    Args:
        body: LoginRequest with email and password.

    Returns:
        Dictionary with access_token, refresh_token, and expires_in.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    # In production, fetch db_user from the database by email
    db_user = _get_user_from_db(body.email)
    try:
        return login(body.email, body.password, db_user)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/auth/logout", tags=["auth"])
def logout_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Invalidate the current session (token blacklist in production).

    Args:
        current_user: Injected by get_current_user dependency.

    Returns:
        Confirmation message.
    """
    # In production: add token jti to a Redis blacklist
    return {"message": "Logged out successfully."}


# --- Order routes ---

@router.post("/orders", tags=["orders"])
def create_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Create a new order for the authenticated user.

    Args:
        body: CreateOrderRequest with items list and currency.
        current_user: Injected authenticated user.

    Returns:
        Created order dict with id, status, and total_amount.

    Raises:
        HTTPException 400: If items list is empty or prices are invalid.
    """
    if not body.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item.")
    # Stub — real logic would persist to DB via database/connection.py
    return {"order_id": "ord_stub_123", "status": "pending", "total_amount": 0.0}


@router.get("/orders/{order_id}", tags=["orders"])
def get_order(order_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    """
    Retrieve an order by ID. Users can only see their own orders unless admin.

    Args:
        order_id: The order UUID.
        current_user: Injected authenticated user.

    Returns:
        Order dict.

    Raises:
        HTTPException 404: If order not found.
        HTTPException 403: If user doesn't own the order and isn't admin.
    """
    order = _get_order_from_db(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    return order


# --- Payment routes ---

@router.post("/payments/charge", tags=["payments"])
def charge_endpoint(
    body: PaymentRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Process a payment for an existing order.

    Args:
        body: PaymentRequest with order_id, amount, currency, and payment_method_id.
        current_user: Injected authenticated user.

    Returns:
        Transaction result dict from process_payment.

    Raises:
        HTTPException 400: If payment validation fails or gateway declines.
    """
    try:
        return process_payment(
            amount=body.amount,
            currency=body.currency,
            payment_method_id=body.payment_method_id,
            order_id=body.order_id,
            metadata=body.metadata,
        )
    except (PaymentError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payments/refund", tags=["payments"])
def refund_endpoint(
    body: RefundRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Issue a refund for a captured transaction. Requires billing role.

    Args:
        body: RefundRequest with transaction_id and optional partial amount.
        current_user: Injected authenticated user (must have 'billing' role).

    Returns:
        Refund result dict.

    Raises:
        HTTPException 403: If user lacks billing role.
        HTTPException 400: If refund fails.
    """
    if "billing" not in current_user.get("roles", []) and "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Billing or admin role required.")
    try:
        return process_refund(body.transaction_id, body.amount)
    except (PaymentError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Admin routes ---

@router.get("/admin/users", tags=["admin"])
def list_users(current_user: dict = Depends(get_current_user)) -> list:
    """
    List all users. Requires admin role.

    Args:
        current_user: Injected authenticated user (must have 'admin' role).

    Returns:
        List of user dicts.

    Raises:
        HTTPException 403: If user is not an admin.
    """
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required.")
    return []  # Stub


# --- Internal stubs ---
def _get_user_from_db(email: str) -> Optional[dict]:
    return None  # Stub

def _get_order_from_db(order_id: str) -> Optional[dict]:
    return None  # Stub
