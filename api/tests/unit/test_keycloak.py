import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.core.keycloak import KeycloakClient
import asyncio

# Fixtures for mocking
@pytest.fixture
def mock_keycloak_admin():
    with patch("src.core.keycloak.KeycloakAdmin") as mock_admin:
        yield mock_admin

@pytest.fixture
def mock_keycloak_openid():
    with patch("src.core.keycloak.KeycloakOpenID") as mock_openid:
        yield mock_openid

@pytest.fixture
def keycloak_client(mock_keycloak_admin, mock_keycloak_openid):
    # Initialize the client. The __init__ calls KeycloakOpenID and KeycloakAdmin
    client = KeycloakClient()
    return client

@pytest.mark.asyncio
async def test_verify_token_success(keycloak_client):
    # Setup mock return value for decode_token
    token_payload = {
        "iss": "http://testserver:8081/realms/master",
        "aud": ["account", "api-backend"],
        "sub": "user-123"
    }
    
    # We must patch the settings inside the client instance to match our mock token
    with patch("src.core.keycloak.settings") as mock_settings:
        mock_settings.KEYCLOAK_ISSUER_URL = "http://testserver:8081"
        mock_settings.KEYCLOAK_REALM = "master"
        mock_settings.KEYCLOAK_CLIENT_ID = "api-backend"
        
        keycloak_client.client.decode_token.return_value = token_payload
        
        result = await keycloak_client.verify_token("valid_token")
        
        assert result is not None
        assert result["sub"] == "user-123"

@pytest.mark.asyncio
async def test_verify_token_invalid_issuer(keycloak_client):
    token_payload = {
        "iss": "http://wrong-issuer/realms/master",
        "aud": ["api-backend"]
    }
    
    with patch("src.core.keycloak.settings") as mock_settings:
        mock_settings.KEYCLOAK_ISSUER_URL = "http://testserver:8081"
        mock_settings.KEYCLOAK_REALM = "master"
        mock_settings.KEYCLOAK_CLIENT_ID = "api-backend"
        
        keycloak_client.client.decode_token.return_value = token_payload
        
        result = await keycloak_client.verify_token("invalid_token")
        
        assert result is None

@pytest.mark.asyncio
async def test_create_user_in_keycloak(keycloak_client):
    # Mock the admin client methods
    admin_mock = keycloak_client.admin_client
    admin_mock.create_user.return_value = "new-user-id"
    admin_mock.get_realm_role.return_value = {"id": "role-id-123"}
    
    result = await keycloak_client.create_user_in_keycloak(
        username="testuser",
        email="test@example.com",
        password="password123",
        first_name="Test",
        last_name="User",
        realm_role="student",
        nmec="12345"
    )
    
    assert result["user_id"] == "new-user-id"
    admin_mock.create_user.assert_called_once()
    
    # Check that create_user was called with correct payload including nmec
    call_args = admin_mock.create_user.call_args[0][0]
    assert call_args["username"] == "testuser"
    assert call_args["attributes"]["nmec"] == "12345"
    
    admin_mock.assign_realm_roles.assert_called_once_with(
        user_id="new-user-id",
        roles=[{"id": "role-id-123", "name": "student"}]
    )

@pytest.mark.asyncio
async def test_create_user_in_keycloak_duplicate(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.create_user.side_effect = Exception("User exists with same username")
    
    with pytest.raises(ValueError, match="already exists"):
        await keycloak_client.create_user_in_keycloak(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

def test_role_and_group_checks(keycloak_client):
    token_info = {
        "realm_access": {
            "roles": ["student", "default-roles"]
        },
        "groups": ["/s1/students", "/w1/vigilant"]
    }
    
    assert keycloak_client.has_role(token_info, "student") is True
    assert keycloak_client.has_role(token_info, "manager") is False
    
    assert keycloak_client.has_group(token_info, "/s1/students") is True
    assert keycloak_client.has_group(token_info, "/s2/students") is False

@pytest.mark.asyncio
async def test_create_subject_groups(keycloak_client):
    admin_mock = keycloak_client.admin_client
    
    # Mock create_group to return a fake ID based on the group name
    def mock_create_group(payload):
        return f"id-{payload['name'].replace('/', '-')}"
    
    admin_mock.create_group.side_effect = mock_create_group
    admin_mock.get_user.return_value = {"username": "regent_user"}
    
    result = await keycloak_client.create_subject_groups_and_assign_regent(
        subject_id="99",
        regent_keycloak_id="regent-123"
    )
    
    assert result is True
    # 10 subgroups to create
    assert admin_mock.create_group.call_count == 10
    
    # Verify regent assignment
    admin_mock.group_user_add.assert_called_once_with("regent-123", "id-s99-regent")

@pytest.mark.asyncio
async def test_get_user_group_paths(keycloak_client):
    admin_mock = keycloak_client.admin_client
    
    admin_mock.get_user_groups.return_value = [
        {"id": "1", "name": "regent", "path": "/s1/regent"},
        {"id": "2", "name": "students", "path": "/s2/students"}
    ]
    
    paths = await keycloak_client.get_user_group_paths("user-123")
    
    assert len(paths) == 2
    assert "/s1/regent" in paths
    assert "/s2/students" in paths
