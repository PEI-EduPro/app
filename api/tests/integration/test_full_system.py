import pytest
import pytest_asyncio
import uuid
import time
from httpx import AsyncClient, ASGITransport
from keycloak import KeycloakAdmin, KeycloakOpenID
from src.main import app
from src.core.settings import settings
from src.core.db import init_db

# --- Fixtures for Real Services ---

@pytest.fixture(scope="module")
def keycloak_admin_master():
    """Connects to Keycloak Admin on the master realm."""
    return KeycloakAdmin(
        server_url=settings.KEYCLOAK_SERVER_URL,
        username=settings.KEYCLOAK_ADMIN_USERNAME,
        password=settings.KEYCLOAK_ADMIN_PASSWORD,
        realm_name="master",
        verify=True
    )

@pytest.fixture(scope="module")
def keycloak_admin_edupro(keycloak_admin_master):
    """
    Connects to Keycloak Admin targeting 'edupro' realm, 
    but using the authenticated session/token from master admin.
    """
    return KeycloakAdmin(
        server_url=settings.KEYCLOAK_SERVER_URL,
        username=settings.KEYCLOAK_ADMIN_USERNAME,
        password=settings.KEYCLOAK_ADMIN_PASSWORD,
        realm_name="edupro",        # The realm we want to manage
        user_realm_name="master",   # The realm the user belongs to
        verify=True
    )

@pytest.fixture(scope="module")
def keycloak_openid():
    """Connects to Keycloak OpenID for token generation."""
    return KeycloakOpenID(
        server_url=settings.KEYCLOAK_SERVER_URL,
        client_id="frontend",
        realm_name="edupro"
    )

@pytest_asyncio.fixture(scope="function")
async def test_manager_user(keycloak_admin_edupro):
    """
    Creates a temporary Manager user in 'edupro' realm.
    Yields the user info.
    Cleans up after test.
    """
    username = f"test_manager_{uuid.uuid4().hex[:8]}"
    password = "testpassword12345"
    email = f"{username}@example.com"
    
    # 1. Create User
    user_payload = {
        "username": username,
        "email": email,
        "firstName": "Test",
        "lastName": "Manager",
        "enabled": True,
        "emailVerified": True
    }
    
    # create_user will now definitely target edupro
    user_id = keycloak_admin_edupro.create_user(user_payload)
    
    # Explicitly set password
    keycloak_admin_edupro.set_user_password(user_id, password, temporary=False)
    
    # Ensure no required actions are pending (like Update Password)
    keycloak_admin_edupro.update_user(user_id, {"requiredActions": []})
    
    # Small delay to ensure Keycloak processes the credentials
    time.sleep(1)
    
    # 2. Assign 'manager' Role
    manager_role = keycloak_admin_edupro.get_realm_role("manager")
    keycloak_admin_edupro.assign_realm_roles(user_id=user_id, roles=[manager_role])
    
    user_info = {
        "id": user_id,
        "username": username,
        "password": password,
        "email": email
    }
    
    yield user_info
    
    # Teardown
    keycloak_admin_edupro.delete_user(user_id)

@pytest_asyncio.fixture(scope="function")
async def manager_token(keycloak_openid, test_manager_user):
    """Gets a valid access token for the test manager."""
    token = keycloak_openid.token(
        username=test_manager_user["username"],
        password=test_manager_user["password"]
    )
    return token["access_token"]

@pytest_asyncio.fixture(scope="function")
async def real_api_client():
    """
    Client connected to the real app (no mocks).
    Assumes DB and Keycloak are running at localhost ports.
    """
    # Ensure no dependency overrides (in case other tests ran)
    app.dependency_overrides = {}
    
    # Initialize DB tables
    await init_db()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# --- Integration Test ---

@pytest.mark.asyncio
async def test_create_and_delete_subject_full_integration(
    real_api_client, 
    manager_token, 
    test_manager_user, 
    keycloak_admin_edupro
):
    """
    End-to-End Test:
    1. Authenticate as Manager.
    2. Create Subject (API).
    3. Verify Subject in DB (API).
    4. Verify Groups in Keycloak.
    5. Delete Subject (API).
    6. Verify Cleanup.
    """
    
    headers = {"Authorization": f"Bearer {manager_token}"}
    
    # --- Step 1: Create Subject ---
    subject_name = f"Integration Subject {uuid.uuid4().hex[:6]}"
    payload = {
        "name": subject_name,
        "regent_keycloak_id": test_manager_user["id"]
    }
    
    response = await real_api_client.post("/api/subjects/", json=payload, headers=headers)
    assert response.status_code == 200, f"Create Subject failed: {response.text}"
    subject_data = response.json()
    subject_id = subject_data["id"]
    assert subject_data["name"] == subject_name
    
    # --- Step 2: Verify Keycloak Groups ---
    expected_regent_group = f"s{subject_id}/regent"
    
    # Fetch all groups (or search)
    groups = keycloak_admin_edupro.get_groups()
    
    def find_group(name, group_list):
        for g in group_list:
            if g['name'] == name:
                return g
        return None

    regent_group = find_group(expected_regent_group, groups)
    assert regent_group is not None, f"Group {expected_regent_group} not found in Keycloak"
    
    # Verify User is in the Regent Group
    members = keycloak_admin_edupro.get_group_members(regent_group['id'])
    member_ids = [m['id'] for m in members]
    assert test_manager_user['id'] in member_ids, "Manager user not found in subject regent group"
    
    # --- Step 3: Delete Subject ---
    del_response = await real_api_client.delete(f"/api/subjects/{subject_id}", headers=headers)
    assert del_response.status_code == 204, f"Delete failed: {del_response.text}"
    
    # --- Step 4: Verify Cleanup ---
    # 1. API: Subject should be gone
    get_response = await real_api_client.get(f"/api/subjects/{subject_id}", headers=headers)
    assert get_response.status_code == 404
    
    # 2. Keycloak: Groups should be gone
    # Refresh groups list
    groups_after = keycloak_admin_edupro.get_groups()
    regent_group_after = find_group(expected_regent_group, groups_after)
    assert regent_group_after is None, f"Group {expected_regent_group} should have been deleted"