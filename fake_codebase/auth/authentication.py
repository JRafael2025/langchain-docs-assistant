"""
Authentication module — handles login, token generation, and session management.
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional

import jwt

SECRET_KEY = "super-secret-key-change-in-production"
TOKEN_EXPIRY_HOURS = 8
REFRESH_TOKEN_EXPIRY_DAYS = 30


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""
    pass


def hash_password(password: str, salt: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    Args:
        password: Plain text password.
        salt: Random salt string (store alongside the hash).

    Returns:
        Hex-encoded password hash.
    """
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return dk.hex()


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """
    Verify a plain text password against a stored hash.

    Args:
        password: Plain text password provided by the user.
        salt: Salt used when the hash was originally created.
        stored_hash: The hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


def generate_access_token(user_id: int, email: str, roles: list[str]) -> str:
    """
    Generate a signed JWT access token.

    Args:
        user_id: Database ID of the authenticated user.
        email: User's email address (included as a claim).
        roles: List of role strings, e.g. ["admin", "billing"].

    Returns:
        Signed JWT string valid for TOKEN_EXPIRY_HOURS hours.
    """
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def generate_refresh_token(user_id: int) -> str:
    """
    Generate a long-lived refresh token for silent re-authentication.

    Args:
        user_id: Database ID of the user.

    Returns:
        Signed JWT string valid for REFRESH_TOKEN_EXPIRY_DAYS days.
    """
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT string to decode.

    Returns:
        Decoded payload as a dictionary.

    Raises:
        TokenExpiredError: If the token has passed its expiry time.
        AuthenticationError: If the token signature is invalid or malformed.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired. Please refresh.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")


def login(email: str, password: str, db_user: dict) -> dict:
    """
    Authenticate a user and return access + refresh tokens.

    Args:
        email: Email provided at login.
        password: Plain text password provided at login.
        db_user: User record fetched from the database, must contain
                 'id', 'password_hash', 'salt', 'roles', 'is_active'.

    Returns:
        Dictionary with 'access_token', 'refresh_token', and 'expires_in'.

    Raises:
        AuthenticationError: If credentials are wrong or account is inactive.
    """
    if not db_user:
        raise AuthenticationError("Invalid email or password.")

    if not db_user.get("is_active"):
        raise AuthenticationError("Account is deactivated. Contact support.")

    if not verify_password(password, db_user["salt"], db_user["password_hash"]):
        raise AuthenticationError("Invalid email or password.")

    access_token = generate_access_token(db_user["id"], email, db_user["roles"])
    refresh_token = generate_refresh_token(db_user["id"])

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": TOKEN_EXPIRY_HOURS * 3600,
        "token_type": "Bearer",
    }


def refresh_session(refresh_token: str) -> dict:
    """
    Issue a new access token using a valid refresh token.

    Args:
        refresh_token: A previously issued refresh token.

    Returns:
        New access token dictionary (same shape as login response).

    Raises:
        AuthenticationError: If the refresh token is invalid or not of type 'refresh'.
    """
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise AuthenticationError("Token is not a refresh token.")

    # In a real system you'd re-fetch the user from the DB here
    return generate_access_token(payload["sub"], "", [])
