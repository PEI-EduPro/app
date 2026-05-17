import pytest
from unittest.mock import patch, AsyncMock
from src.main import app
from src.core.deps import get_current_user_info
from src.models.subject import Subject
from src.models.exam_config import ExamConfig

@pytest.mark.asyncio
async def test_get_exam_config_warnings_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/warnings/9999")
    assert response.status_code == 404
    assert "Exam configuration not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_exam_config_warnings_exception(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    with patch("src.routers.warning.get_warnings_by_exam_config_id", side_effect=Exception("Boom")):
        response = await client.get(f"/api/warnings/{ec.id}")
        assert response.status_code == 500
        assert "Failed to fetch warnings" in response.json()["detail"]

@pytest.mark.asyncio
async def test_resolve_exam_config_warnings_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/warnings/9999/resolve", json={"assignments": []})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_resolve_exam_config_warnings_exception(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    with patch("src.routers.warning.resolve_warnings_service", side_effect=Exception("Boom")):
        response = await client.post(f"/api/warnings/{ec.id}/resolve", json={"assignments": []})
        assert response.status_code == 500
