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
    KEYCLOAK_REALM: str = Field(default="EduPro")  # Match your realm name
    KEYCLOAK_CLIENT_ID: str = Field(default="api-backend")
    KEYCLOAK_CLIENT_SECRET: str = Field(default="RdwcPv5Gp0Nq3Pm8fGV4HfpST4KurVhb")
    KEYCLOAK_PUBLIC_KEY: str = Field(default="")
    
    @property
    def PGSQL_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()