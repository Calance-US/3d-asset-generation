"""
Authentication endpoints for JWT token management and user operations.

This module provides endpoints for:
- User login and authentication
- Token validation and refresh
- User information retrieval
- Logout functionality
"""

import logging
from typing import Any, Dict

from app.auth.dependencies import get_current_user, get_current_user_optional
from app.auth.jwt_utils import get_token_info
from app.auth.keycloak_client import get_keycloak_client
from app.config.settings import settings
from app.models import User
from app.schemas.schemas import UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Returns:
        UserResponse: Current user details
    """
    return UserResponse.from_user(current_user)  # type: ignore


@router.post("/validate-token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Validate JWT token and return token information.

    Args:
        credentials: HTTP bearer token credentials

    Returns:
        Dict[str, Any]: Token validation result and information
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_info = get_token_info(credentials.credentials)

    if not token_info["valid"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=token_info.get("error", "Invalid token"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "valid": token_info["valid"],
        "expired": token_info["expired"],
        "remaining_time": token_info["remaining_time"],
        "user_info": token_info["user_info"],
        "claims_valid": token_info["claims_valid"],
    }


@router.get("/config")
async def get_auth_config() -> Dict[str, Any]:
    """
    Get authentication configuration for frontend.

    Returns:
        Dict[str, Any]: Authentication configuration
    """
    if not settings.AUTH_ENABLED:
        return {
            "auth_enabled": False,
            "auth_provider": None,
            "login_url": None,
            "logout_url": None,
        }

    try:
        keycloak_client = get_keycloak_client()
        well_known = keycloak_client.get_well_known_config()

        return {
            "auth_enabled": True,
            "auth_provider": "keycloak",
            "server_url": settings.KEYCLOAK_SERVER_URL,
            "realm": settings.KEYCLOAK_REALM,
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "authorization_endpoint": well_known.get("authorization_endpoint"),
            "token_endpoint": well_known.get("token_endpoint"),
            "userinfo_endpoint": well_known.get("userinfo_endpoint"),
            "end_session_endpoint": well_known.get("end_session_endpoint"),
            "jwks_uri": well_known.get("jwks_uri"),
        }
    except Exception as e:
        logger.error(f"Failed to get auth config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


@router.get("/health")
async def auth_health_check() -> Dict[str, Any]:
    """
    Check authentication service health.

    Returns:
        Dict[str, Any]: Health status
    """
    if not settings.AUTH_ENABLED:
        return {
            "status": "disabled",
            "message": "Authentication is disabled",
        }

    try:
        keycloak_client = get_keycloak_client()
        healthy = keycloak_client.health_check()

        return {
            "status": "healthy" if healthy else "unhealthy",
            "keycloak_server": settings.KEYCLOAK_SERVER_URL,
            "realm": settings.KEYCLOAK_REALM,
            "message": "Authentication service is operational"
            if healthy
            else "Authentication service is not responding",
        }
    except Exception as e:
        logger.error(f"Auth health check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
        }


@router.post("/introspect")
async def introspect_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Introspect token with Keycloak.

    Args:
        credentials: HTTP bearer token credentials

    Returns:
        Dict[str, Any]: Token introspection result
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        keycloak_client = get_keycloak_client()
        result = keycloak_client.introspect_token(credentials.credentials)
        return result
    except Exception as e:
        logger.error(f"Token introspection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token introspection failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/user-info")
async def get_user_info_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get user information from Keycloak using token.

    Args:
        credentials: HTTP bearer token credentials

    Returns:
        Dict[str, Any]: User information from Keycloak
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        keycloak_client = get_keycloak_client()
        user_info = keycloak_client.get_user_info(credentials.credentials)
        return user_info
    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to retrieve user information",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get user profile information (works with or without authentication).

    Args:
        current_user: Current authenticated user (optional)

    Returns:
        Dict[str, Any]: User profile information
    """
    if not current_user:
        return {
            "authenticated": False,
            "user": None,
            "auth_enabled": settings.AUTH_ENABLED,
        }

    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "external_id": current_user.external_id,
            "provider": current_user.provider,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "is_admin": current_user.is_admin_user(),
            "is_active": current_user.is_active_user(),
            "last_login": current_user.last_login.isoformat()
            if current_user.last_login  # type: ignore
            else None,
        },
        "auth_enabled": settings.AUTH_ENABLED,
    }


@router.post("/logout")
async def logout_user() -> Dict[str, str]:
    """
    Logout endpoint (client-side token removal).

    Since we're using JWT tokens, logout is primarily handled client-side
    by removing the token. This endpoint provides logout URL for proper
    Keycloak session termination.

    Returns:
        Dict[str, str]: Logout information
    """
    try:
        keycloak_client = get_keycloak_client()
        well_known = keycloak_client.get_well_known_config()

        logout_url = well_known.get("end_session_endpoint")
        if logout_url:
            # Add redirect URI if needed
            redirect_uri = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/account"
            logout_url_with_redirect = f"{logout_url}?redirect_uri={redirect_uri}"

            return {
                "message": "Logout successful",
                "logout_url": logout_url_with_redirect,
            }
        else:
            return {
                "message": "Logout successful",
                "logout_url": "",
            }
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return {
            "message": "Logout completed (service unavailable)",
            "logout_url": "",
        }
