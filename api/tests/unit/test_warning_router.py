import pytest
from unittest.mock import patch, AsyncMock
from src.main import app
from src.core.deps import get_current_user_info
from src.models.subject import Subject
from src.models.exam_config import ExamConfig
from src.models.waiting_room import WaitingRoom

@pytest.mark.asyncio
async def test_get_waiting_room_warnings_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/warnings/9999")
    assert response.status_code == 404
    assert "Waiting room not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_waiting_room_warnings_config_not_found(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    await session.commit()
    
    # Mock session.get to return None for ExamConfig
    from sqlalchemy.ext.asyncio import AsyncSession
    with patch.object(AsyncSession, "get", side_effect=[wr, None]):
        response = await client.get(f"/api/warnings/{wr.id}")
        assert response.status_code == 404
        assert "Exam configuration not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_waiting_room_warnings_exception(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    await session.commit()
    
    with patch("src.routers.warning.get_warnings_by_waiting_room_id", side_effect=Exception("Boom")):
        response = await client.get(f"/api/warnings/{wr.id}")
        assert response.status_code == 500
        assert "Failed to fetch warnings" in response.json()["detail"]

@pytest.mark.asyncio
async def test_resolve_waiting_room_warnings_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/warnings/9999/resolve", json={"assignments": []})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_resolve_waiting_room_warnings_config_not_found(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    await session.commit()
    
    from sqlalchemy.ext.asyncio import AsyncSession
    with patch.object(AsyncSession, "get", side_effect=[wr, None]):
        response = await client.post(f"/api/warnings/{wr.id}/resolve", json={"assignments": []})
        assert response.status_code == 404
        assert "Exam configuration not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_resolve_waiting_room_warnings_exception(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    await session.commit()
    
    with patch("src.routers.warning.resolve_warnings_service", side_effect=Exception("Boom")):
        response = await client.post(f"/api/warnings/{wr.id}/resolve", json={"assignments": []})
        assert response.status_code == 500
