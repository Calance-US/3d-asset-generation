import logging
from typing import Any, Dict, Optional

from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakError

from app.config.settings import settings

logger = logging.getLogger(__name__)


class KeycloakClient:
    """
    Keycloak client for handling authentication operations.

    This class provides methods for:
    - JWT token validation
    - User information retrieval
    - Public key management
    - Token introspection
    """

    def __init__(self):
        """Initialize Keycloak OpenID and Admin clients."""
        try:
            self.openid = KeycloakOpenID(
                server_url=settings.KEYCLOAK_SERVER_URL,
                client_id=settings.KEYCLOAK_CLIENT_ID,
                realm_name=settings.KEYCLOAK_REALM,
                client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
            )

            self.admin = KeycloakAdmin(
                server_url=settings.KEYCLOAK_SERVER_URL,
                username=settings.KEYCLOAK_ADMIN_USERNAME,
                password=settings.KEYCLOAK_ADMIN_PASSWORD,
                realm_name=settings.KEYCLOAK_REALM,
                verify=True,
            )

            logger.info("Keycloak client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Keycloak client: {str(e)}")
            raise

    def get_public_key(self) -> str:
        """
        Get the public key for JWT verification.

        Returns:
            str: The public key for token verification

        Raises:
            KeycloakError: If unable to retrieve public key
        """
        try:
            public_key = self.openid.public_key()
            if not public_key:
                raise KeycloakError("Public key is empty")
            return public_key
        except Exception as e:
            logger.error(f"Failed to get public key: {str(e)}")
            raise KeycloakError(f"Unable to retrieve public key: {str(e)}")

    def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and introspect a token.

        Args:
            token (str): The JWT token to introspect

        Returns:
            Dict[str, Any]: Token introspection result

        Raises:
            KeycloakError: If token introspection fails
        """
        try:
            result = self.openid.introspect(token)
            if not result.get("active", False):
                raise KeycloakError("Token is not active")
            return result
        except Exception as e:
            logger.error(f"Token introspection failed: {str(e)}")
            raise KeycloakError(f"Token introspection failed: {str(e)}")

    def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from a valid token.

        Args:
            token (str): Valid JWT token

        Returns:
            Dict[str, Any]: User information

        Raises:
            KeycloakError: If unable to retrieve user info
        """
        try:
            user_info = self.openid.userinfo(token)
            return user_info
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise KeycloakError(f"Unable to retrieve user info: {str(e)}")

    def get_user_roles(self, user_id: str) -> list:
        """
        Get user roles from Keycloak.

        Args:
            user_id (str): Keycloak user ID

        Returns:
            list: List of user roles

        Raises:
            KeycloakError: If unable to retrieve user roles
        """
        try:
            roles = self.admin.get_realm_roles_of_user(user_id)
            return [role["name"] for role in roles]
        except Exception as e:
            logger.error(f"Failed to get user roles for {user_id}: {str(e)}")
            raise KeycloakError(f"Unable to retrieve user roles: {str(e)}")

    def get_well_known_config(self) -> Dict[str, Any]:
        """
        Get the well-known OpenID configuration.

        Returns:
            Dict[str, Any]: OpenID configuration
        """
        try:
            return self.openid.well_known()
        except Exception as e:
            logger.error(f"Failed to get well-known config: {str(e)}")
            raise KeycloakError(f"Unable to retrieve configuration: {str(e)}")

    def health_check(self) -> bool:
        """
        Perform a health check on the Keycloak connection.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            # Try to get the well-known configuration as a health check
            self.get_well_known_config()
            return True
        except Exception as e:
            logger.warning(f"Keycloak health check failed: {str(e)}")
            return False


# Singleton instance
keycloak_client: Optional[KeycloakClient] = None


def get_keycloak_client() -> KeycloakClient:
    """
    Get the singleton Keycloak client instance.

    Returns:
        KeycloakClient: The Keycloak client instance
    """
    global keycloak_client
    if keycloak_client is None:
        keycloak_client = KeycloakClient()
    return keycloak_client
