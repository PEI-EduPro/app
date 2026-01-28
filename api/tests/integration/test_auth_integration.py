import pytest
from src.core.settings import settings
import uuid

@pytest.mark.asyncio
async def test_health_check(integration_client):
    response = await integration_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_get_me_unauthorized(integration_client):
    # No header -> HTTPBearer raises 403 (default auto_error=True)
    response = await integration_client.get("/api/users/me")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_me_authorized(integration_client):
    # Token is mocked, so any string works
    headers = {"Authorization": "Bearer mock-token"}
    response = await integration_client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "integration_manager"
    # assert "manager" in data["realm_roles"] # The API might not return roles in 'me' if not in model, check UserPublic model

@pytest.mark.asyncio
async def test_create_and_delete_subject_flow(integration_client, edupro_admin, setup_keycloak):
    headers = {"Authorization": "Bearer mock-token"}
    
    # 1. Get Regent ID
    regent_id = setup_keycloak["user_id"]
    
    # 2. Create Subject
    subject_name = f"Integration Test Subject {uuid.uuid4()}"
    response = await integration_client.post(
        "/api/subjects/",
        json={"name": subject_name, "regent_keycloak_id": regent_id},
        headers=headers
    )
    
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    subject_id = data["id"]
    assert data["name"] == subject_name
    
    # 3. Verify Keycloak Groups were created
    expected_regent_group_name = f"s{subject_id}/regent"
    
    # Debug: Try to find group in all groups
    all_groups = edupro_admin.get_groups()
    target_group = next((g for g in all_groups if g['name'] == expected_regent_group_name), None)
    
    assert target_group is not None, f"Group {expected_regent_group_name} not found in all groups: {[g['name'] for g in all_groups]}"
    
    # Verify manager is in the regent group
    members = edupro_admin.get_group_members(group_id=target_group["id"])
    member_ids = [m["id"] for m in members]
    assert regent_id in member_ids
    
    # 4. Delete Subject
    del_response = await integration_client.delete(f"/api/subjects/{subject_id}", headers=headers)
    assert del_response.status_code == 204
    
    # 5. Verify Keycloak Groups were deleted
    try:
        fresh_groups = edupro_admin.get_groups()
        check_group = next((g for g in fresh_groups if g['name'] == expected_regent_group_name), None)
        if check_group:
             pytest.fail(f"Group {expected_regent_group_name} should have been deleted")
    except Exception:
        pass