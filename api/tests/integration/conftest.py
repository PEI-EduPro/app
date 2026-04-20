import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from keycloak import KeycloakAdmin, KeycloakOpenID
from src.main import app
from src.core.settings import settings
from src.core.db import get_session
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from unittest.mock import patch, AsyncMock
from src.core.keycloak import KeycloakClient

# Use the real database for integration tests
DB_URL = settings.PGSQL_DATABASE_URI

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(DB_URL, echo=False, future=True)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def real_db_session(db_engine):
    async with db_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture(scope="session")
def edupro_admin():
    # Connect to Master realm to authenticate, but manage 'edupro' realm
    return KeycloakAdmin(
        server_url=settings.KEYCLOAK_SERVER_URL,
        username=settings.KEYCLOAK_ADMIN_USERNAME,
        password=settings.KEYCLOAK_ADMIN_PASSWORD,
        realm_name=settings.KEYCLOAK_REALM, # edupro
        user_realm_name="master", # authenticate as admin in master
        verify=True
    )

@pytest.fixture(scope="session")
def setup_keycloak(edupro_admin):
    # Ensure 'manager' role exists (it should)
    try:
        edupro_admin.get_realm_role("manager")
    except Exception:
        pytest.fail("Role 'manager' not found in edupro realm!")

    # Create/Get a user to act as the subject of our tests
    manager_username = "integration_manager"
    user_id = edupro_admin.get_user_id(manager_username)
    
    if not user_id:
        user_id = edupro_admin.create_user({
            "email": "manager@integration.test",
            "username": manager_username,
            "enabled": True,
            "emailVerified": True
        })
    
    # Assign 'manager' role
    role = edupro_admin.get_realm_role("manager")
    user_roles = edupro_admin.get_realm_roles_of_user(user_id)
    if not any(r['name'] == 'manager' for r in user_roles):
        edupro_admin.assign_realm_roles(user_id=user_id, roles=[role])
        
    return {"manager_username": manager_username, "user_id": user_id}

@pytest_asyncio.fixture(scope="function")
async def integration_client(real_db_session, edupro_admin, setup_keycloak):
    async def override_get_session():
        yield real_db_session
        
    app.dependency_overrides[get_session] = override_get_session
    
    # Create a mock KeycloakClient that:
    # 1. Uses the REAL admin client (edupro_admin) for group operations
    # 2. Mocks verify_token to return our setup user (bypassing login issues)
    
    mock_kc = KeycloakClient()
    mock_kc.admin_client = edupro_admin
    
    # Mock verify_token
    async def mock_verify(token):
        return {
            "sub": setup_keycloak["user_id"],
            "preferred_username": setup_keycloak["manager_username"],
            "email": "manager@integration.test",
            "realm_access": {"roles": ["manager"]},
            "groups": [],
            "iss": f"{settings.KEYCLOAK_ISSUER_URL}/realms/{settings.KEYCLOAK_REALM}",
            "aud": ["account", settings.KEYCLOAK_CLIENT_ID]
        }
    
    mock_kc.verify_token = mock_verify
    
    # Patch where it is used
    with patch("src.core.deps.keycloak_client", mock_kc), \
         patch("src.routers.user.keycloak_client", mock_kc), \
         patch("src.services.subject.keycloak_client", mock_kc):
         
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        
    app.dependency_overrides.clear()
