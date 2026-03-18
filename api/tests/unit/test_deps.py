import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.core.deps import (
    get_current_user_info,
    require_role,
    require_group,
    verify_permission,
    verify_regent_exists
)
from src.models.user import User

@pytest.fixture
def mock_keycloak_client():
    with patch("src.core.deps.keycloak_client") as mock_kc:
        yield mock_kc

@pytest.mark.asyncio
async def test_get_current_user_info_success(mock_keycloak_client):
    # Setup
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    mock_keycloak_client.verify_token = AsyncMock(return_value={
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "realm_access": {"roles": ["student"]}
    })
    mock_keycloak_client.get_user_group_paths = AsyncMock(return_value=["/s1/students"])

    # Execution
    user = await get_current_user_info(credentials)

    # Assertion
    assert isinstance(user, User)
    assert user.user_id == "user-123"
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert "student" in user.realm_roles
    assert "/s1/students" in user.groups

@pytest.mark.asyncio
async def test_get_current_user_info_no_credentials():
    with pytest.raises(HTTPException) as exc:
        await get_current_user_info(None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"

@pytest.mark.asyncio
async def test_get_current_user_info_invalid_token(mock_keycloak_client):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
    mock_keycloak_client.verify_token = AsyncMock(return_value=None)
    
    with pytest.raises(HTTPException) as exc:
        await get_current_user_info(credentials)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"

@pytest.mark.asyncio
async def test_get_current_user_info_fallback_groups(mock_keycloak_client):
    # If get_user_group_paths fails, it should fallback to token groups
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    mock_keycloak_client.verify_token = AsyncMock(return_value={
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "groups": ["/token/group"]
    })
    mock_keycloak_client.get_user_group_paths = AsyncMock(side_effect=Exception("Failed to fetch"))

    user = await get_current_user_info(credentials)
    
    assert user.groups == ["/token/group"]

@pytest.mark.asyncio
async def test_require_role_success():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=["manager"], groups=[])
    dep = require_role("manager")
    
    result = await dep(user_info=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_role_failure():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=["student"], groups=[])
    dep = require_role("manager")
    
    with pytest.raises(HTTPException) as exc:
        await dep(user_info=user)
    assert exc.value.status_code == 403
    assert "Requires manager role" in exc.value.detail

@pytest.mark.asyncio
async def test_require_group_success():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=[], groups=["/s1/regent"])
    dep = require_group("/s1/regent")
    
    result = await dep(user_info=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_group_failure():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=[], groups=["/s2/regent"])
    dep = require_group("/s1/regent")
    
    with pytest.raises(HTTPException) as exc:
        await dep(user_info=user)
    assert exc.value.status_code == 403

def test_verify_permission_exact_match():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=[], groups=["/s1/regent"])
    
    assert verify_permission(user, ["/s1/regent"]) is True

def test_verify_permission_role_match():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=["manager"], groups=[])
    
    # Manager is in the allowed list
    assert verify_permission(user, ["manager"]) is True
    
    # Manager is allowed implicitly via flag
    assert verify_permission(user, ["/s1/regent"], allow_manager=True) is True

def test_verify_permission_prefix_match():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=[], groups=["/s1/add_students"])
    
    # Any group starting with /s1/
    assert verify_permission(user, ["/s1"]) is True

def test_verify_permission_denied():
    user = User(user_id="1", username="test", email="test@example.com", realm_roles=["student"], groups=["/s2/students"])
    
    with pytest.raises(HTTPException) as exc:
        verify_permission(user, ["/s1/regent", "/s1/add_students"])
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_verify_regent_exists_success(mock_keycloak_client):
    import asyncio
    # Need to mock the inner admin_client structure properly for the sync executor call
    class MockAdmin:
        def get_user(self, user_id):
            return {"id": user_id, "username": "regent_mock"}
    
    mock_keycloak_client.admin_client = MockAdmin()
    
    result = await verify_regent_exists("valid_regent_id")
    assert result["username"] == "regent_mock"

@pytest.mark.asyncio
async def test_verify_regent_exists_failure(mock_keycloak_client):
    class MockAdmin:
        def get_user(self, user_id):
            raise Exception("User not found")
            
    mock_keycloak_client.admin_client = MockAdmin()
    
    with pytest.raises(HTTPException) as exc:
        await verify_regent_exists("invalid_regent_id")
    assert exc.value.status_code == 400
    assert "not found in Keycloak" in exc.value.detail
