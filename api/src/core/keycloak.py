import asyncio
from keycloak import KeycloakOpenID
from src.core.settings import settings

class KeycloakClient:
    def __init__(self):
        self.client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        )

    async def verify_token(self, token: str):
        """Verify JWT token and return user info"""
        try:
            # Run the synchronous keycloak operation in a thread pool
            loop = asyncio.get_event_loop()
            token_info = await loop.run_in_executor(
                None, 
                lambda: self.client.decode_token(token)
            )
            return token_info
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

    def get_user_roles(self, token_info: dict) -> list[str]:
        """Extract user roles from token"""
        realm_access = token_info.get("realm_access", {})
        return realm_access.get("roles", [])

    def has_role(self, token_info: dict, role: str) -> bool:
        """Check if user has specific role"""
        roles = self.get_user_roles(token_info)
        return role in roles

keycloak_client = KeycloakClient()