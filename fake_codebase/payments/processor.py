"""
Payment processor — core logic for transactions, refunds, and validation.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from database.models import Order, Transaction


class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentError(Exception):
    """Base class for payment-related errors."""
    pass


class InsufficientFundsError(PaymentError):
    """Raised when the payment method has insufficient funds."""
    pass


class InvalidCurrencyError(PaymentError):
    """Raised when an unsupported currency is requested."""
    pass


SUPPORTED_CURRENCIES = {"USD", "EUR", "BRL", "GBP", "CAD"}
MAX_TRANSACTION_AMOUNT = 100_000.00


def validate_payment_data(amount: float, currency: str) -> None:
    """
    Validate amount and currency before processing.

    Args:
        amount: Transaction amount (must be positive and below max limit).
        currency: ISO 4217 currency code.

    Raises:
        ValueError: If amount is invalid.
        InvalidCurrencyError: If currency is not supported.
    """
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}.")
    if amount > MAX_TRANSACTION_AMOUNT:
        raise ValueError(f"Amount {amount} exceeds max allowed {MAX_TRANSACTION_AMOUNT}.")
    if currency.upper() not in SUPPORTED_CURRENCIES:
        raise InvalidCurrencyError(f"Currency '{currency}' not supported. Use: {SUPPORTED_CURRENCIES}")


def process_payment(
    amount: float,
    currency: str,
    payment_method_id: str,
    order_id: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Process a payment transaction end-to-end.

    This function validates input, calls the payment gateway, records the
    transaction in the database, and returns a structured result.

    Args:
        amount: Amount to charge, in the smallest unit of the currency
                (e.g. cents for USD).
        currency: ISO 4217 currency code (e.g. 'USD', 'BRL').
        payment_method_id: Gateway token representing the customer's saved
                           payment method.
        order_id: Internal order ID this payment is associated with.
        metadata: Optional extra key/value pairs to attach to the transaction
                  record (e.g. customer_id, promo_code).

    Returns:
        Dictionary with keys:
            - transaction_id (str): UUID of the created transaction.
            - status (str): Final status string from PaymentStatus enum.
            - amount (float): Charged amount.
            - currency (str): Currency used.
            - created_at (str): ISO timestamp of transaction creation.

    Raises:
        ValueError: If amount or currency are invalid.
        InvalidCurrencyError: If currency is not in SUPPORTED_CURRENCIES.
        PaymentError: If the gateway declines or returns an error.
    """
    validate_payment_data(amount, currency)

    transaction_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    # Gateway call stub — replaced by gateway.py in real usage
    gateway_response = _call_gateway(payment_method_id, amount, currency)

    if not gateway_response["success"]:
        raise PaymentError(f"Gateway declined: {gateway_response.get('error')}")

    return {
        "transaction_id": transaction_id,
        "status": PaymentStatus.CAPTURED.value,
        "amount": amount,
        "currency": currency.upper(),
        "order_id": order_id,
        "gateway_reference": gateway_response["reference"],
        "metadata": metadata or {},
        "created_at": created_at,
    }


def process_refund(transaction_id: str, amount: Optional[float] = None) -> dict:
    """
    Refund a previously captured transaction, in full or partially.

    Args:
        transaction_id: UUID of the original transaction to refund.
        amount: Amount to refund. If None, the full transaction amount is
                refunded. Must not exceed the original charge.

    Returns:
        Dictionary with refund details and updated transaction status.

    Raises:
        PaymentError: If the transaction is not found or already fully refunded.
        ValueError: If the refund amount exceeds the original charge.
    """
    # Stub: in production, fetch the original transaction from the DB
    original = _fetch_transaction(transaction_id)

    if original["status"] == PaymentStatus.REFUNDED.value:
        raise PaymentError(f"Transaction {transaction_id} is already fully refunded.")

    refund_amount = amount if amount is not None else original["amount"]

    if refund_amount > original["amount"]:
        raise ValueError(
            f"Refund amount {refund_amount} exceeds original charge {original['amount']}."
        )

    is_partial = refund_amount < original["amount"]
    new_status = PaymentStatus.PARTIALLY_REFUNDED if is_partial else PaymentStatus.REFUNDED

    return {
        "refund_id": str(uuid.uuid4()),
        "transaction_id": transaction_id,
        "refund_amount": refund_amount,
        "status": new_status.value,
        "created_at": datetime.utcnow().isoformat(),
    }


def get_transaction_status(transaction_id: str) -> dict:
    """
    Retrieve the current status of a transaction.

    Args:
        transaction_id: UUID of the transaction to look up.

    Returns:
        Dictionary with transaction details and current status.
    """
    return _fetch_transaction(transaction_id)


# --- Internal helpers ---

def _call_gateway(payment_method_id: str, amount: float, currency: str) -> dict:
    """Stub for the actual gateway HTTP call (see gateway.py)."""
    return {"success": True, "reference": f"gw_{uuid.uuid4().hex[:12]}"}


def _fetch_transaction(transaction_id: str) -> dict:
    """Stub for DB fetch — returns a fake transaction record."""
    return {
        "transaction_id": transaction_id,
        "amount": 99.90,
        "currency": "USD",
        "status": PaymentStatus.CAPTURED.value,
    }
