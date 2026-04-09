"""
Validators — reusable input validation helpers used across the codebase.
"""

import re
from typing import Any, Optional


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")
UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_email(email: str) -> str:
    """
    Validate and normalise an email address.

    Args:
        email: Raw email string from user input.

    Returns:
        Lowercased, stripped email string.

    Raises:
        ValidationError: If the email format is invalid.
    """
    cleaned = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValidationError("email", f"'{cleaned}' is not a valid email address.")
    return cleaned


def validate_password_strength(password: str) -> None:
    """
    Enforce minimum password strength requirements.

    Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one digit
        - At least one special character from: !@#$%^&*

    Args:
        password: Plain text password to validate.

    Raises:
        ValidationError: If any requirement is not met.
    """
    if len(password) < 8:
        raise ValidationError("password", "Must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("password", "Must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("password", "Must contain at least one digit.")
    if not re.search(r"[!@#$%^&*]", password):
        raise ValidationError("password", "Must contain at least one special character (!@#$%^&*).")


def validate_phone(phone: str) -> str:
    """
    Validate an international phone number (E.164 format).

    Args:
        phone: Phone number string, with or without leading +.

    Returns:
        Cleaned phone string.

    Raises:
        ValidationError: If format doesn't match E.164.
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
    if not PHONE_REGEX.match(cleaned):
        raise ValidationError("phone", f"'{cleaned}' is not a valid E.164 phone number.")
    return cleaned


def validate_uuid(value: str, field_name: str = "id") -> str:
    """
    Validate that a string is a valid UUID v4.

    Args:
        value: String to validate.
        field_name: Name of the field (used in error message).

    Returns:
        Lowercased UUID string.

    Raises:
        ValidationError: If the string is not a valid UUID.
    """
    cleaned = value.strip().lower()
    if not UUID_REGEX.match(cleaned):
        raise ValidationError(field_name, f"'{cleaned}' is not a valid UUID.")
    return cleaned


def validate_positive_amount(amount: Any, field_name: str = "amount") -> float:
    """
    Validate that a value is a positive numeric amount.

    Args:
        amount: Value to validate (int or float).
        field_name: Field name for error messages.

    Returns:
        Float value of the amount.

    Raises:
        ValidationError: If the value is not numeric or not positive.
    """
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValidationError(field_name, f"Must be a number, got '{amount}'.")
    if value <= 0:
        raise ValidationError(field_name, f"Must be greater than 0, got {value}.")
    return value


def validate_required_fields(data: dict, required: list[str]) -> None:
    """
    Ensure all required keys are present and non-empty in a dict.

    Args:
        data: Dictionary of input fields.
        required: List of field names that must be present and non-None.

    Raises:
        ValidationError: On the first missing or empty field found.
    """
    for field in required:
        if field not in data or data[field] is None or data[field] == "":
            raise ValidationError(field, "This field is required.")
