import pytest
from unittest.mock import patch, AsyncMock
from src.main import app
from src.core.deps import get_current_user_info
from src.models.user import User
from src.models.exam_config import ExamConfig

def _regent_user():
    return User(
        user_id="regent-id",
        username="regent",
        email="regent@test.com",
        realm_roles=["professor"],
        groups=["/s1/regent"],
    )

@pytest.mark.asyncio
async def test_update_vigilantes_success(client, session):
    # Setup test data - Subject is needed because of foreign key
    from src.models.subject import Subject
    subject = Subject(id=1, name="Test Subject")
    session.add(subject)
    await session.commit()
    
    exam_config = ExamConfig(id=1, subject_id=1, fraction=50)
    session.add(exam_config)
    await session.commit()
    
    app.dependency_overrides[get_current_user_info] = _regent_user
    
    # We need to mock the service because it interacts with Keycloak
    with patch("src.routers.exam.update_exam_session_vigilants_service", new_callable=AsyncMock) as mock_service:
        response = await client.patch("/api/exams/1/vigilantes", json={"vigilant_keycloak_ids": ["v1", "v2"]})
        
        assert response.status_code == 200
        assert response.json()["message"] == "Vigilantes updated successfully."
        mock_service.assert_called_once_with(
            exam_config_id=1,
            vigilant_ids=["v1", "v2"]
        )
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_update_vigilantes_not_found(client, session):
    app.dependency_overrides[get_current_user_info] = _regent_user
    
    response = await client.patch("/api/exams/999/vigilantes", json={"vigilant_keycloak_ids": ["v1"]})
    assert response.status_code == 404
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_update_vigilantes_unauthorized(client, session):
    # Setup test data
    from src.models.subject import Subject
    subject = Subject(id=1, name="Test Subject")
    session.add(subject)
    await session.commit()
    
    exam_config = ExamConfig(id=1, subject_id=1, fraction=50)
    session.add(exam_config)
    await session.commit()
    
    # User with no permissions for subject 1
    def _other_user():
        return User(
            user_id="other-id",
            username="other",
            email="other@test.com",
            realm_roles=["professor"],
            groups=["/s2/regent"],
        )
    
    app.dependency_overrides[get_current_user_info] = _other_user
    
    response = await client.patch("/api/exams/1/vigilantes", json={"vigilant_keycloak_ids": ["v1"]})
    assert response.status_code == 403
    
    app.dependency_overrides.clear()
