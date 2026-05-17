import pytest
from httpx import AsyncClient
from src.main import app
from src.core.deps import get_current_user_info
from src.models.user import User
from src.models.subject import Subject
from src.models.exam_config import ExamConfig, ExamState
from src.models.topic import Topic
from src.models.topic_config import TopicConfig

@pytest.mark.asyncio
async def test_get_exam_config_endpoint_success(client, session):
    # 1. Create a subject
    sub = Subject(name="Test Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    # 2. Create an exam config
    config = ExamConfig(subject_id=sub.id, fraction=100, state=ExamState.PREPARING)
    session.add(config)
    await session.commit()
    await session.refresh(config)

    # 3. Mock user as regent
    user = User(
        user_id="prof-id",
        username="prof",
        email="prof@test.com",
        realm_roles=["professor"],
        groups=[f"/s{sub.id}/regent"],
    )
    app.dependency_overrides[get_current_user_info] = lambda: user

    # 4. Call the endpoint
    response = await client.get(f"/api/exams/config/{config.id}")

    # 5. Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == config.id
    assert data["subject_id"] == sub.id
    assert data["fraction"] == 100

@pytest.mark.asyncio
async def test_get_exam_config_endpoint_forbidden(client, session):
    # 1. Create a subject
    sub = Subject(name="Test Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    # 2. Create an exam config
    config = ExamConfig(subject_id=sub.id, fraction=100, state=ExamState.PREPARING)
    session.add(config)
    await session.commit()
    await session.refresh(config)

    # 3. Mock user as DIFFERENT subject regent
    user = User(
        user_id="prof-id",
        username="prof",
        email="prof@test.com",
        realm_roles=["professor"],
        groups=[f"/s{sub.id + 1}/regent"],
    )
    app.dependency_overrides[get_current_user_info] = lambda: user

    # 4. Call the endpoint
    response = await client.get(f"/api/exams/config/{config.id}")

    # 5. Assertions
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_exam_config_endpoint_not_found(client, session):
    # 1. Mock user
    user = User(
        user_id="prof-id",
        username="prof",
        email="prof@test.com",
        realm_roles=["professor"],
        groups=["/s1/regent"],
    )
    app.dependency_overrides[get_current_user_info] = lambda: user

    # 2. Call the endpoint for non-existent ID
    response = await client.get("/api/exams/config/9999")

    # 3. Assertions
    assert response.status_code == 404
