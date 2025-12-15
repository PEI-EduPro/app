# src/core/settings.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="myuser")
    POSTGRES_PASSWORD: str = Field(default="mypassword")
    POSTGRES_DB: str = Field(default="mydatabase")
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str = Field(default="http://localhost:8080")
    KEYCLOAK_REALM: str = Field(default="master")
    KEYCLOAK_CLIENT_ID: str = Field(default="api-backend")
    KEYCLOAK_CLIENT_SECRET: str = Field(default="**********") # Make sure this is the secret for 'api-backend' in 'master' realm
    KEYCLOAK_PUBLIC_KEY: str = Field(default="")
    # Note: These are for the initial admin-cli authentication method.
    # The preferred method is service account as described below.
    KEYCLOAK_ADMIN_USERNAME: str = Field(default="admin") # Default admin username
    KEYCLOAK_ADMIN_PASSWORD: str = Field(default="admin") # Default admin password

    @property
    def PGSQL_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()