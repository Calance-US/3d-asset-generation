"""
Authentication dependencies for FastAPI endpoints.

This module provides dependency functions to handle JWT token validation,
user authentication, and authorization for API endpoints.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.keycloak_client import get_keycloak_client
from app.config.settings import settings
from app.database.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

# Security scheme for bearer token
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error exception."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error exception."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user from JWT token (optional).

    This dependency allows endpoints to work with or without authentication.
    Returns None if no valid token is provided.

    Args:
        request: FastAPI request object
        credentials: HTTP bearer token credentials
        db: Database session

    Returns:
        Optional[User]: The authenticated user or None
    """
    if not settings.AUTH_ENABLED:
        # Return system user when auth is disabled
        return (
            db.query(User).filter(User.external_id == "system-migration-user").first()
        )

    if settings.AUTH_BYPASS_DEVELOPMENT and settings.ENVIRONMENT == "development":
        # In development mode with bypass enabled, return system user
        return (
            db.query(User).filter(User.external_id == "system-migration-user").first()
        )

    if not credentials or not credentials.credentials:
        return None

    try:
        return await validate_token_and_get_user(credentials.credentials, db)
    except Exception as e:
        logger.warning(f"Optional authentication failed: {str(e)}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token (required).

    Args:
        credentials: HTTP bearer token credentials
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        AuthenticationError: If authentication fails
    """
    if not settings.AUTH_ENABLED:
        # Return system user when auth is disabled
        user = (
            db.query(User).filter(User.external_id == "system-migration-user").first()
        )
        if not user:
            raise AuthenticationError("System user not found")
        return user

    if settings.AUTH_BYPASS_DEVELOPMENT and settings.ENVIRONMENT == "development":
        # In development mode with bypass enabled, return system user
        user = (
            db.query(User).filter(User.external_id == "system-migration-user").first()
        )
        if not user:
            raise AuthenticationError("System user not found")
        return user

    if not credentials or not credentials.credentials:
        raise AuthenticationError("Missing authentication token")

    try:
        return await validate_token_and_get_user(credentials.credentials, db)
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise AuthenticationError("Invalid authentication token")


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated admin user.

    Args:
        current_user: The authenticated user

    Returns:
        User: The authenticated admin user

    Raises:
        AuthorizationError: If user is not an admin
    """
    if not current_user.is_admin_user():
        raise AuthorizationError("Admin access required")
    return current_user


async def validate_token_and_get_user(token: str, db: Session) -> User:
    """
    Validate JWT token and get or create user.

    Args:
        token: JWT token to validate
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        AuthenticationError: If token validation fails
    """
    try:
        keycloak_client = get_keycloak_client()

        # Validate token with Keycloak
        token_info = keycloak_client.introspect_token(token)
        if not token_info.get("active", False):
            raise AuthenticationError("Token is not active")

        # Get user info from Keycloak
        user_info = keycloak_client.get_user_info(token)

        # Extract user details
        external_id = user_info.get("sub")
        email = user_info.get("email")
        username = user_info.get("preferred_username", email)

        # Extract roles from Keycloak token
        realm_access = token_info.get("realm_access", {})
        roles = realm_access.get("roles", [])

        # Determine primary role (admin takes precedence)
        if "admin" in roles or "super_admin" in roles:
            primary_role = "admin" if "admin" in roles else "super_admin"
        elif "educator" in roles:
            primary_role = "educator"
        else:
            primary_role = "student"

        if not external_id:
            raise AuthenticationError("Invalid user information in token")

        # Check if user exists in our database
        user = db.query(User).filter(User.external_id == external_id).first()

        if not user:
            # Create new user
            user = User(
                external_id=external_id,
                provider="keycloak",
                username=username or email or "unknown",
                email=email,
                role=primary_role,
                last_login=datetime.now(),
                is_deleted=False,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info(
                f"Created new user: {email} (External ID: {external_id}, Role: {primary_role})"
            )
        else:
            # Update user info if needed
            updated = False
            if email and user.email != email:
                user.email = email  # type: ignore
                updated = True
            if username and user.username != username:
                user.username = username  # type: ignore
                updated = True
            if user.role != primary_role:  # type: ignore
                user.role = primary_role  # type: ignore
                updated = True

            # Update last login (always update)
            user.last_login = datetime.now()  # type: ignore
            updated = True

            if updated:
                db.commit()
                db.refresh(user)
                logger.info(f"Updated user info: {email}, Role: {primary_role}")

        if user.is_deleted:  # type: ignore
            raise AuthenticationError("User account is disabled")

        return user

    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise AuthenticationError("Token validation failed")


def check_user_permission(user: User, required_permission: str) -> bool:
    """
    Check if user has required permission.

    Args:
        user: User to check permissions for
        required_permission: Permission string to check

    Returns:
        bool: True if user has permission, False otherwise
    """
    # Admin users have all permissions
    if user.is_admin_user():
        return True

    # Role-based permissions
    educator_permissions = [
        "visualizations:read",
        "visualizations:create",
        "visualizations:edit",
        "visualizations:delete",
        "history:read",
        "history:delete",
        "prompts:read",
        "prompts:create",
        "prompts:edit",
        "prompts:delete",
    ]

    student_permissions = [
        "visualizations:read",
        "visualizations:create",
        "history:read",
        "prompts:read",
    ]

    if user.role == "educator":  # type: ignore
        return not user.is_deleted and required_permission in educator_permissions  # type: ignore
    elif user.role == "student":  # type: ignore
        return not user.is_deleted and required_permission in student_permissions  # type: ignore

    return False


def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions.

    Args:
        permission: Required permission string

    Returns:
        Dependency function that checks the permission
    """

    async def permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not check_user_permission(current_user, permission):
            raise AuthorizationError(f"Permission '{permission}' required")
        return current_user

    return permission_dependency
