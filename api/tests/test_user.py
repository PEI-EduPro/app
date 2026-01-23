import pytest
from src.core.deps import get_current_user_info
from src.main import app

@pytest.mark.asyncio
async def test_get_me(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    response = await client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "manager"
    assert data["email"] == "manager@example.com"

@pytest.mark.asyncio
async def test_create_user(client, mock_auth):
    # This endpoint interacts with Keycloak (mocked)
    from src.core.keycloak import keycloak_client
    from unittest.mock import AsyncMock

    app.dependency_overrides[get_current_user_info] = mock_auth
    
    # Mock Keycloak create_user
    with pytest.MonkeyPatch.context() as mp:
        async_mock = AsyncMock(return_value={"user_id": "new-user-id", "message": "created"})
        mp.setattr(keycloak_client, "create_user_in_keycloak", async_mock)

        response = await client.post(
            "/api/users/create",
            json={
                "username": "newstudent",
                "email": "student@test.com",
                "password": "pass",
                "first_name": "New",
                "last_name": "Student",
                "realm_role": "student"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newstudent"
        async_mock.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_unauthorized(client):
    # Mock a non-manager user
    from src.models.user import User
    student_user = User(user_id="s1", username="stu", email="s@t.com", realm_roles=["student"], groups=[])
    
    async def mock_student():
        return student_user
        
    app.dependency_overrides[get_current_user_info] = mock_student
    
    response = await client.post(
        "/api/users/create",
        json={
            "username": "hacker",
            "email": "h@h.com",
            "password": "p",
            "first_name": "H",
            "last_name": "R"
        }
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_user_duplicate(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    from src.core.keycloak import keycloak_client
    from unittest.mock import AsyncMock
    
    # Mock Keycloak to raise ValueError (simulating duplicate)
    with pytest.MonkeyPatch.context() as mp:
        async_mock = AsyncMock(side_effect=ValueError("User already exists"))
        mp.setattr(keycloak_client, "create_user_in_keycloak", async_mock)

        response = await client.post(
            "/api/users/create",
            json={
                "username": "existing",
                "email": "e@e.com",
                "password": "p",
                "first_name": "E",
                "last_name": "E"
            }
        )
        assert response.status_code == 400
        assert "User already exists" in response.json()["detail"]
