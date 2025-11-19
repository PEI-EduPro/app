# src/core/keycloak.py
import asyncio
from keycloak import KeycloakOpenID, KeycloakAdmin # Import KeycloakAdmin
from src.core.settings import settings
import logging

logger = logging.getLogger(__name__)

class KeycloakClient:
    def __init__(self):
        self.client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID, # 'api-backend'
            realm_name=settings.KEYCLOAK_REALM,    # 'master'
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET, # Secret for 'api-backend'
        )
        
        # Initialize the Keycloak Admin client using the 'api-backend' client credentials
        # This assumes 'api-backend' client is configured as 'confidential' in the 'master' realm
        # and has admin roles assigned to its service account via 'realm-management'.
        try:
            self.admin_client = KeycloakAdmin(
                server_url=settings.KEYCLOAK_SERVER_URL,
                username=settings.KEYCLOAK_ADMIN_USERNAME, # 'admin'
                password=settings.KEYCLOAK_ADMIN_PASSWORD, # 'admin'
                realm_name=settings.KEYCLOAK_REALM,        # 'master'
                client_id="admin-cli",                     # Default admin client
            )
            logger.info("Keycloak Admin client (via Service Account) initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak Admin client: {e}")
            # Depending on your needs, you might want to prevent startup or handle gracefully
            self.admin_client = None
            self.admin_init_error = e

        # Pre-fetch the public key for token verification (optional, might be done by OpenID client)
        try:
            public_key = self.client.public_key()
            logger.info("Keycloak client public key fetched successfully.")
        except Exception as e:
            logger.error(f"Failed to fetch Keycloak client public key: {e}")

    async def verify_token(self, token: str) -> dict | None:
        """Verify JWT token using the Keycloak client's built-in method."""
        logger.debug(f"Starting verification for token: {token[:50]}...")

        try:
            loop = asyncio.get_event_loop()
            # Use the simplest form of decode_token that works with your library version
            token_info = await loop.run_in_executor(
                None,
                lambda: self.client.decode_token(token)
            )
            
            # Manual issuer verification
            expected_issuer = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
            actual_issuer = token_info.get('iss', '')
            
            if actual_issuer != expected_issuer:
                logger.error(f"Issuer mismatch. Expected: {expected_issuer}, Got: {actual_issuer}")
                return None
            
            # Manual audience check - allow both 'account' and the client ID
            allowed_audiences = ['account', settings.KEYCLOAK_CLIENT_ID]
            token_audience = token_info.get('aud', [])
            
            # Handle both string and list audience formats
            if isinstance(token_audience, str):
                token_audience = [token_audience]
            
            if not any(aud in allowed_audiences for aud in token_audience):
                logger.error(f"Audience mismatch. Expected one of {allowed_audiences}, Got: {token_audience}")
                return None
            
            logger.info(f"Token verified successfully for user: {token_info.get('preferred_username', token_info.get('sub', 'unknown'))}")
            logger.debug(f"Full token info: {token_info}")
            return token_info

        except Exception as e:
            # Catch all errors during verification
            logger.error(f"Token verification failed with error: {e}")
            logger.exception(e)  # Log the full traceback
            return None

    async def create_user_in_keycloak(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = None,
        last_name: str = None,
        temporary: bool = False,
        realm_role: str = None
    ) -> dict:
        """
        Create a new user in Keycloak using the Admin API via Service Account.
        Optionally assign a realm role.
        """
        # Check if admin client was initialized successfully
        if not self.admin_client:
            logger.error(f"Cannot create user: Admin client not initialized. Error during init: {getattr(self, 'admin_init_error', 'Unknown error')}")
            raise RuntimeError("Keycloak Admin client not available. Check server logs and configuration.")

        logger.info(f"Attempting to create user: {username} in realm: {settings.KEYCLOAK_REALM}")
        try:
            loop = asyncio.get_event_loop()
            user_id = await loop.run_in_executor(
                None,
                lambda: self.admin_client.create_user({
                    "username": username,
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "enabled": True, # Enable user by default
                    "emailVerified": True, # Assume email is verified during creation
                    "credentials": [
                        {
                            "type": "password",
                            "value": password,
                            "temporary": temporary # Set temporary flag
                        }
                    ]
                })
            )
            logger.info(f"User {username} created successfully with ID: {user_id}")

            # Assign realm role if specified
            if realm_role:
                logger.info(f"Attempting to assign role '{realm_role}' to user {username} (ID: {user_id})")
                # Get the role ID first
                role_id = await loop.run_in_executor(
                    None,
                    lambda: self.admin_client.get_realm_role(realm_role)['id']
                )
                # Assign the role
                await loop.run_in_executor(
                    None,
                    lambda: self.admin_client.assign_realm_roles(
                        user_id=user_id,
                        roles=[{"id": role_id, "name": realm_role}]
                    )
                )
                logger.info(f"Role '{realm_role}' assigned to user {username} successfully.")

            return {"user_id": user_id, "message": "User created successfully"}

        except Exception as e:
            # Catch all errors during creation
            # Common errors might be KeycloakGetError, KeycloakPostError, etc. depending on the library version
            error_msg = str(e)
            logger.error(f"Keycloak Admin API error during user creation: {error_msg}")
            logger.exception(e) # Log the full traceback

            # Handle specific errors like user already exists, role not found, etc.
            # These error messages can vary depending on the Keycloak server version and python-keycloak version
            if "User exists with same username" in error_msg or "User exists with same email" in error_msg:
                 raise ValueError(f"User with username '{username}' or email '{email}' already exists.")
            if "Role not found" in error_msg or "Role with name" in error_msg and "does not exist" in error_msg:
                 raise ValueError(f"Realm role '{realm_role}' not found.")
            # Raise a generic error for other issues
            raise e # Re-raise to be handled by the endpoint


    def get_user_roles(self, token_info: dict) -> list[str]:
        """Extract user roles from token"""
        realm_access = token_info.get("realm_access", {})
        return realm_access.get("roles", [])

    def get_user_groups(self, token_info: dict) -> list[str]:
        """Extract user groups from token"""
        return token_info.get("groups", [])

    def has_role(self, token_info: dict, role: str) -> bool:
        """Check if user has specific role"""
        roles = self.get_user_roles(token_info)
        return role in roles

    def has_group(self, token_info: dict, group: str) -> bool:
        """Check if user is in specific group"""
        groups = self.get_user_groups(token_info)
        return group in groups

keycloak_client = KeycloakClient()