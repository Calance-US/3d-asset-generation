"""
JWT utilities for token handling and validation.

This module provides utilities for JWT token operations including:
- Token decoding and validation
- Public key management
- Token claims extraction
- Token expiration checking
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from keycloak.exceptions import KeycloakError

from app.auth.keycloak_client import get_keycloak_client
from app.config.settings import settings

logger = logging.getLogger(__name__)


class JWTError(Exception):
    """Custom JWT error exception."""

    pass


class TokenExpiredError(JWTError):
    """Token has expired."""

    pass


class TokenInvalidError(JWTError):
    """Token is invalid."""

    pass


def decode_token(token: str, verify_signature: bool = True) -> Dict[str, Any]:
    """
    Decode JWT token and validate its signature.

    Args:
        token (str): JWT token to decode
        verify_signature (bool): Whether to verify token signature

    Returns:
        Dict[str, Any]: Decoded token payload

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
        JWTError: If token decoding fails
    """
    try:
        if verify_signature:
            # Get public key from Keycloak
            keycloak_client = get_keycloak_client()
            public_key = keycloak_client.get_public_key()

            # Format public key for JWT validation
            formatted_key = (
                f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
            )

            # Decode and validate token
            payload = jwt.decode(
                token,
                formatted_key,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                },
            )
        else:
            # Decode without verification (for development/testing)
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                },
            )

        return payload

    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise TokenExpiredError("Token has expired")
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise TokenInvalidError(f"Invalid token: {str(e)}")
    except KeycloakError as e:
        logger.error(f"Keycloak error during token validation: {str(e)}")
        raise JWTError(f"Token validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token decoding: {str(e)}")
        raise JWTError(f"Token decoding failed: {str(e)}")


def extract_user_info(token_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from JWT token payload.

    Args:
        token_payload (Dict[str, Any]): Decoded JWT payload

    Returns:
        Dict[str, Any]: User information dictionary
    """
    return {
        "user_id": token_payload.get("sub"),
        "username": token_payload.get("preferred_username"),
        "email": token_payload.get("email"),
        "first_name": token_payload.get("given_name", ""),
        "last_name": token_payload.get("family_name", ""),
        "roles": token_payload.get("realm_access", {}).get("roles", []),
        "client_roles": token_payload.get("resource_access", {})
        .get(settings.KEYCLOAK_CLIENT_ID, {})
        .get("roles", []),
        "issued_at": token_payload.get("iat"),
        "expires_at": token_payload.get("exp"),
        "not_before": token_payload.get("nbf"),
        "audience": token_payload.get("aud"),
        "issuer": token_payload.get("iss"),
    }


def is_token_expired(token_payload: Dict[str, Any]) -> bool:
    """
    Check if token has expired.

    Args:
        token_payload (Dict[str, Any]): Decoded JWT payload

    Returns:
        bool: True if token has expired, False otherwise
    """
    exp = token_payload.get("exp")
    if not exp:
        return True

    # Convert timestamp to datetime
    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    return now >= exp_datetime


def get_token_remaining_time(token_payload: Dict[str, Any]) -> Optional[int]:
    """
    Get remaining time until token expires.

    Args:
        token_payload (Dict[str, Any]): Decoded JWT payload

    Returns:
        Optional[int]: Remaining seconds until expiration, None if no expiration
    """
    exp = token_payload.get("exp")
    if not exp:
        return None

    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    if now >= exp_datetime:
        return 0

    return int((exp_datetime - now).total_seconds())


def validate_token_claims(token_payload: Dict[str, Any]) -> bool:
    """
    Validate token claims and structure.

    Args:
        token_payload (Dict[str, Any]): Decoded JWT payload

    Returns:
        bool: True if token claims are valid, False otherwise
    """
    required_claims = ["sub", "email", "iat", "exp"]

    for claim in required_claims:
        if claim not in token_payload:
            logger.warning(f"Missing required claim: {claim}")
            return False

    # Validate audience if configured
    if settings.JWT_AUDIENCE:
        aud = token_payload.get("aud")
        if isinstance(aud, list):
            if settings.JWT_AUDIENCE not in aud:
                logger.warning(f"Invalid audience: {aud}")
                return False
        elif aud != settings.JWT_AUDIENCE:
            logger.warning(f"Invalid audience: {aud}")
            return False

    # Validate issuer format
    iss = token_payload.get("iss")
    if iss and not iss.startswith(settings.KEYCLOAK_SERVER_URL):
        logger.warning(f"Invalid issuer: {iss}")
        return False

    return True


def extract_bearer_token(authorization_header: str) -> Optional[str]:
    """
    Extract bearer token from Authorization header.

    Args:
        authorization_header (str): Authorization header value

    Returns:
        Optional[str]: Bearer token if found, None otherwise
    """
    if not authorization_header:
        return None

    parts = authorization_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def get_token_info(token: str) -> Dict[str, Any]:
    """
    Get comprehensive token information.

    Args:
        token (str): JWT token

    Returns:
        Dict[str, Any]: Token information including payload and metadata
    """
    try:
        payload = decode_token(token, verify_signature=True)
        user_info = extract_user_info(payload)

        return {
            "valid": True,
            "expired": is_token_expired(payload),
            "remaining_time": get_token_remaining_time(payload),
            "user_info": user_info,
            "payload": payload,
            "claims_valid": validate_token_claims(payload),
        }
    except (TokenExpiredError, TokenInvalidError, JWTError) as e:
        return {
            "valid": False,
            "error": str(e),
            "expired": True,
            "remaining_time": 0,
            "user_info": None,
            "payload": None,
            "claims_valid": False,
        }
