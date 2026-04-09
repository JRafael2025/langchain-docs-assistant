"""
Permissions module — role-based access control (RBAC).
"""

from functools import wraps
from typing import Callable

ROLES_HIERARCHY = {
    "superadmin": 100,
    "admin": 80,
    "billing": 60,
    "support": 40,
    "user": 20,
    "guest": 0,
}


class PermissionDeniedError(Exception):
    """Raised when a user lacks the required role or permission."""
    pass


def get_role_level(role: str) -> int:
    """
    Return the numeric level for a given role name.

    Args:
        role: Role string, e.g. 'admin'.

    Returns:
        Integer level (higher = more permissions). Returns 0 for unknown roles.
    """
    return ROLES_HIERARCHY.get(role, 0)


def has_role(user_roles: list[str], required_role: str) -> bool:
    """
    Check if a user has at least the required role level.

    Args:
        user_roles: List of roles assigned to the user.
        required_role: Minimum role required.

    Returns:
        True if any of the user's roles meets or exceeds the required level.
    """
    required_level = get_role_level(required_role)
    return any(get_role_level(r) >= required_level for r in user_roles)


def require_role(required_role: str) -> Callable:
    """
    Decorator that enforces a minimum role on a route or function.

    Usage:
        @require_role("admin")
        def delete_user(user_id: int, current_user: dict): ...

    Args:
        required_role: Role string the caller must have.

    Returns:
        Decorated function that raises PermissionDeniedError if check fails.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user") or (args[0] if args else None)
            if not current_user:
                raise PermissionDeniedError("No authenticated user in context.")
            if not has_role(current_user.get("roles", []), required_role):
                raise PermissionDeniedError(
                    f"Role '{required_role}' required. User has: {current_user.get('roles')}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def can_access_resource(user_roles: list[str], resource_owner_id: int, user_id: int) -> bool:
    """
    Check if a user can access a resource, either by ownership or admin role.

    Args:
        user_roles: Roles of the requesting user.
        resource_owner_id: ID of the user who owns the resource.
        user_id: ID of the requesting user.

    Returns:
        True if the user owns the resource or has admin-level access.
    """
    if user_id == resource_owner_id:
        return True
    return has_role(user_roles, "admin")


def list_permissions(roles: list[str]) -> dict:
    """
    Return a summary of what actions a set of roles can perform.

    Args:
        roles: List of role strings assigned to a user.

    Returns:
        Dictionary mapping permission names to booleans.
    """
    max_level = max((get_role_level(r) for r in roles), default=0)
    return {
        "can_read": max_level >= ROLES_HIERARCHY["guest"],
        "can_write": max_level >= ROLES_HIERARCHY["user"],
        "can_manage_billing": max_level >= ROLES_HIERARCHY["billing"],
        "can_support": max_level >= ROLES_HIERARCHY["support"],
        "can_admin": max_level >= ROLES_HIERARCHY["admin"],
        "is_superadmin": max_level >= ROLES_HIERARCHY["superadmin"],
    }
