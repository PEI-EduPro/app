import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.core.keycloak import KeycloakClient

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
    client = KeycloakClient()
    return client

@pytest.mark.asyncio
async def test_create_user_in_keycloak_no_admin(mock_keycloak_openid):
    # Force admin_client to be None by simulating init failure
    with patch("src.core.keycloak.KeycloakAdmin", side_effect=Exception("Init fail")):
        client = KeycloakClient()
        with pytest.raises(RuntimeError, match="Admin client not available"):
            await client.create_user_in_keycloak("u", "e", "p")

@pytest.mark.asyncio
async def test_create_user_in_keycloak_role_not_found(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.create_user.return_value = "uid"
    admin_mock.get_realm_role.side_effect = Exception("Role not found")
    with pytest.raises(ValueError, match="not found"):
        await keycloak_client.create_user_in_keycloak("u", "e", "p", realm_role="nonexistent")

@pytest.mark.asyncio
async def test_create_subject_groups_regent_not_found(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.create_group.return_value = "gid"
    admin_mock.get_user.side_effect = Exception("User not found")
    with pytest.raises(ValueError, match="Regent user with ID 'r1' not found"):
        await keycloak_client.create_subject_groups_and_assign_regent("1", "r1")

@pytest.mark.asyncio
async def test_create_subject_groups_regent_group_missing_in_cache(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.create_group.return_value = "gid"
    admin_mock.get_user.return_value = {"username": "regent"}
    # We want to test the case where regent_group_id is None
    # This is tricky because we store it in a local dict in the function.
    # But wait, the function does `subgroup_ids[full_group_name] = subgroup_id`.
    # If create_group succeeds, it's there. 
    # Let's mock create_group to return None for regent group (not very realistic but covers the path).
    admin_mock.create_group.side_effect = lambda payload: None if "regent" in payload["name"] else "gid"
    result = await keycloak_client.create_subject_groups_and_assign_regent("1", "r1")
    assert result is False

@pytest.mark.asyncio
async def test_update_subject_regent_create_fail(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = []
    admin_mock.create_group.return_value = None
    # After creating, it fetches groups again. If still not found, it returns False.
    result = await keycloak_client.update_subject_regent("1", "u1")
    assert result is False

@pytest.mark.asyncio
async def test_get_users_by_role_exception(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_realm_role_members.side_effect = Exception("Fail")
    users = await keycloak_client.get_users_by_role("role")
    assert users == []

@pytest.mark.asyncio
async def test_get_subject_professors_exception(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = [{"name": "s1/professors", "id": "pid"}]
    admin_mock.get_group_members.side_effect = Exception("Fail")
    profs = await keycloak_client.get_subject_professors("1")
    assert profs == []

@pytest.mark.asyncio
async def test_get_subject_regent_no_members(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = [{"name": "s1/regent", "id": "rid"}]
    admin_mock.get_group_members.return_value = []
    with pytest.raises(ValueError, match="No regent assigned"):
        await keycloak_client.get_subject_regent("1")

@pytest.mark.asyncio
async def test_add_students_to_subject_error_adding_one(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = [{"name": "s1/students", "id": "sid"}]
    # Fails for first, succeeds for second
    admin_mock.group_user_add.side_effect = [Exception("Fail"), None]
    await keycloak_client.add_students_to_subject("1", ["u1", "u2"])
    assert admin_mock.group_user_add.call_count == 2

@pytest.mark.asyncio
async def test_replace_subject_professors_success(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = [{"name": "s1/professors", "id": "pid"}]
    admin_mock.get_group_members.return_value = [{"id": "old"}]
    await keycloak_client.replace_subject_professors("1", ["new"])
    admin_mock.group_user_remove.assert_called_with("old", "pid")
    admin_mock.group_user_add.assert_called_with("new", "pid")

@pytest.mark.asyncio
async def test_manage_professor_permissions_remove(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = [
        {"name": "s1/professors", "id": "pid"},
        {"name": "s1/edit_topics", "id": "tid"}
    ]
    # is_active=False should call group_user_remove
    await keycloak_client.manage_professor_permissions("1", "uid", {"edit_topics": False})
    admin_mock.group_user_remove.assert_called_with("uid", "tid")

@pytest.mark.asyncio
async def test_create_waiting_room_groups_add_regent_fail(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.create_group.side_effect = lambda payload: f"id-{payload['name']}"
    admin_mock.group_user_add.side_effect = Exception("Add regent fail")
    # This should log the error but return True if it doesn't re-raise
    # Wait, the code says: `except Exception as e: logger.error(...); raise e` in the outer block
    # but the regent add is inside a nested try-except that just logs.
    result = await keycloak_client.create_waiting_room_groups(1, "r1", [])
    assert result is True

@pytest.mark.asyncio
async def test_delete_waiting_room_groups_partial_not_found(keycloak_client):
    admin_mock = keycloak_client.admin_client
    admin_mock.get_groups.return_value = [{"name": "w1/regent", "id": "rid"}]
    # w1/vigilant not found
    result = await keycloak_client.delete_waiting_room_groups(1)
    assert result is True
    admin_mock.delete_group.assert_called_once_with("rid")
