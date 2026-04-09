"""
Payment gateway integration — Stripe and PayPal adapter layer.
"""

import os
from typing import Optional

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "sk_test_placeholder")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "paypal_placeholder")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "paypal_secret_placeholder")


class GatewayError(Exception):
    """Raised when a payment gateway returns an error."""
    pass


class StripeGateway:
    """
    Adapter for the Stripe Payments API.

    Wraps charge creation, refunds, and payment method retrieval
    behind a consistent interface used by processor.py.
    """

    def __init__(self, api_key: str = STRIPE_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.stripe.com/v1"

    def charge(self, amount: int, currency: str, payment_method: str, description: str = "") -> dict:
        """
        Create a Stripe PaymentIntent and immediately confirm it.

        Args:
            amount: Amount in the smallest currency unit (e.g. cents for USD).
            currency: Lowercase ISO 4217 currency code.
            payment_method: Stripe PaymentMethod ID (pm_xxx).
            description: Optional human-readable description for the charge.

        Returns:
            Dictionary with 'id', 'status', and 'amount' from Stripe.

        Raises:
            GatewayError: If Stripe returns a non-success status.
        """
        # Stub: would use stripe.PaymentIntent.create(...) in production
        return {
            "id": f"pi_stub_{payment_method[:8]}",
            "status": "succeeded",
            "amount": amount,
            "currency": currency,
        }

    def refund(self, charge_id: str, amount: Optional[int] = None) -> dict:
        """
        Issue a full or partial refund via Stripe.

        Args:
            charge_id: Stripe charge or PaymentIntent ID to refund.
            amount: Amount to refund in smallest unit. None = full refund.

        Returns:
            Stripe Refund object as a dictionary.

        Raises:
            GatewayError: If Stripe rejects the refund request.
        """
        return {
            "id": f"re_stub_{charge_id[:8]}",
            "status": "succeeded",
            "amount": amount,
            "charge": charge_id,
        }

    def retrieve_payment_method(self, payment_method_id: str) -> dict:
        """
        Fetch details of a saved payment method from Stripe.

        Args:
            payment_method_id: Stripe PaymentMethod ID.

        Returns:
            Dictionary with card brand, last4, expiry, and billing details.
        """
        return {
            "id": payment_method_id,
            "type": "card",
            "card": {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2026},
        }


class PayPalGateway:
    """
    Adapter for the PayPal Orders API v2.
    """

    def __init__(self, client_id: str = PAYPAL_CLIENT_ID, secret: str = PAYPAL_SECRET):
        self.client_id = client_id
        self.secret = secret
        self.base_url = "https://api-m.paypal.com"
        self._access_token: Optional[str] = None

    def _get_access_token(self) -> str:
        """
        Fetch a short-lived OAuth2 access token from PayPal.

        Returns:
            Bearer token string for use in API calls.
        """
        # Stub: would POST to /v1/oauth2/token in production
        return "paypal_access_token_stub"

    def create_order(self, amount: float, currency: str, reference_id: str) -> dict:
        """
        Create a PayPal order and return the approval URL.

        Args:
            amount: Decimal amount (e.g. 19.99).
            currency: ISO 4217 currency code.
            reference_id: Internal reference ID to track the order.

        Returns:
            Dictionary with 'order_id', 'status', and 'approval_url'.
        """
        return {
            "order_id": f"pp_order_{reference_id[:8]}",
            "status": "CREATED",
            "approval_url": "https://www.paypal.com/checkoutnow?token=stub",
        }

    def capture_order(self, order_id: str) -> dict:
        """
        Capture a PayPal order after buyer approval.

        Args:
            order_id: PayPal order ID returned by create_order.

        Returns:
            Capture result with status and transaction ID.

        Raises:
            GatewayError: If capture fails or order is not in APPROVED state.
        """
        return {
            "order_id": order_id,
            "status": "COMPLETED",
            "transaction_id": f"pp_txn_{order_id[-8:]}",
        }


def get_gateway(provider: str = "stripe"):
    """
    Factory function — return the correct gateway adapter by provider name.

    Args:
        provider: Gateway name, either 'stripe' or 'paypal'.

    Returns:
        An instance of StripeGateway or PayPalGateway.

    Raises:
        ValueError: If provider is not recognized.
    """
    if provider == "stripe":
        return StripeGateway()
    elif provider == "paypal":
        return PayPalGateway()
    else:
        raise ValueError(f"Unknown payment provider: '{provider}'. Use 'stripe' or 'paypal'.")
