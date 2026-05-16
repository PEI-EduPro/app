import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from src.main import app
from src.core.deps import get_current_user_info

@pytest.mark.asyncio
async def test_read_current_user(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/users/me")
    assert response.status_code == 200
    assert response.json()["username"] == "manager"

@pytest.mark.asyncio
async def test_create_user_not_manager(client):
    from src.models.user import User
    student_user = User(user_id="s1", username="stu", email="s@t.com", realm_roles=["student"], groups=[])
    async def mock_student():
        return student_user
    app.dependency_overrides[get_current_user_info] = mock_student
    
    response = await client.post(
        "/api/users/create", 
        json={"username": "newuser", "email": "n@e.com", "password": "pwd", "first_name": "F", "last_name": "L"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_user_success(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.create_user_in_keycloak", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"user_id": "new-uuid"}
        response = await client.post(
            "/api/users/create", 
            json={"username": "newuser", "email": "n@e.com", "password": "pwd", "first_name": "F", "last_name": "L"}
        )
        assert response.status_code == 200
        assert response.json()["user_id"] == "new-uuid"

@pytest.mark.asyncio
async def test_create_user_value_error(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.create_user_in_keycloak", side_effect=ValueError("User exists")):
        response = await client.post(
            "/api/users/create", 
            json={"username": "newuser", "email": "n@e.com", "password": "pwd", "first_name": "F", "last_name": "L"}
        )
        assert response.status_code == 400
        assert "User exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_exception(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.create_user_in_keycloak", side_effect=Exception("Internal")):
        response = await client.post(
            "/api/users/create", 
            json={"username": "newuser", "email": "n@e.com", "password": "pwd", "first_name": "F", "last_name": "L"}
        )
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_get_professors_success(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.get_users_by_role", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [{"id": "p1", "username": "prof1", "email": "p1@e.com", "firstName": "F1", "lastName": "L1"}]
        response = await client.get("/api/users/professors")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["username"] == "prof1"

@pytest.mark.asyncio
async def test_get_professors_exception(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.get_users_by_role", side_effect=Exception("Fail")):
        response = await client.get("/api/users/professors")
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_get_students_success(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.get_users_by_role", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [{"id": "s1", "username": "stu1", "email": "s1@e.com", "firstName": "F1", "lastName": "L1"}]
        response = await client.get("/api/users/students")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["username"] == "stu1"

@pytest.mark.asyncio
async def test_get_students_exception(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.user.keycloak_client.get_users_by_role", side_effect=Exception("Fail")):
        response = await client.get("/api/users/students")
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_debug_token_info(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    # require_manager is also used, mock_auth is a manager
    response = await client.get("/api/users/debug/token-info")
    assert response.status_code == 200
    assert response.json()["username"] == "manager"
