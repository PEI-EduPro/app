import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from unittest.mock import MagicMock, patch, AsyncMock

from src.main import app
from src.core.db import get_session
from src.core.deps import get_current_user_info
from src.models.user import User

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def session(engine):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    TestingSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestingSessionLocal() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    
    # Create a transport for the app
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def manager_user():
    return User(
        user_id="manager-id-123",
        username="manager",
        email="manager@example.com",
        realm_roles=["manager"],
        groups=[]
    )

@pytest.fixture
def mock_auth(manager_user):
    async def override_get_current_user_info():
        return manager_user
    return override_get_current_user_info

@pytest.fixture
def mock_keycloak():
    with patch("src.services.subject.keycloak_client", new_callable=MagicMock) as mock:
        # Configure async methods to return AsyncMock or awaiting logic
        mock.create_subject_groups_and_assign_regent = AsyncMock(return_value=True)
        mock.update_subject_regent = AsyncMock(return_value=True)
        mock.delete_subject_groups = AsyncMock(return_value=True)
        mock.get_subject_students = AsyncMock(return_value=[])
        mock.add_students_to_subject = AsyncMock(return_value=None)
        mock.manage_professor_permissions = AsyncMock(return_value=True)
        mock.remove_professor_from_subject = AsyncMock(return_value=True)
        yield mock

@pytest.fixture
def mock_verify_regent():
    # Patch where it is USED, in the service
    with patch("src.services.subject.verify_regent_exists", new_callable=AsyncMock) as mock:
        mock.return_value = {"username": "regent_user", "id": "regent-123"}
        yield mock
