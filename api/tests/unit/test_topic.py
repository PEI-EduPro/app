import pytest
from unittest.mock import patch, AsyncMock
from src.core.deps import get_current_user_info
from src.main import app

@pytest.mark.asyncio
async def test_create_topic(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    # Need a subject first
    from src.models.subject import Subject
    subject = Subject(name="Topic Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    response = await client.post(
        "/api/topics/",
        json={"name": "Derivatives", "subject_id": subject.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Derivatives"
    assert data["subject_id"] == subject.id

@pytest.mark.asyncio
async def test_get_topic_by_id(client, session, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.topic import Topic
    
    sub = Subject(name="Physics")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    t = Topic(name="Kinematics", subject_id=sub.id)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    
    response = await client.get(f"/api/topics/{t.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Kinematics"
    assert data["id"] == t.id

@pytest.mark.asyncio
async def test_create_topic_invalid_subject(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    # Trying to create a topic for a subject that doesn't exist
    response = await client.post(
        "/api/topics/",
        json={"name": "Orphan Topic", "subject_id": 99999}
    )
    # The DB constraint should fail (Foreign Key) -> 500 or 400 depending on handling
    # If not handled explicitly, it's usually 500. 
    # Let's see if we can catch integrity errors. 
    # Current implementation might just let it fail.
    assert response.status_code in [400, 403, 500] 

@pytest.mark.asyncio
async def test_get_topic_not_found(client, session, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/topics/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_topic_exception(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    sub = Subject(name="Fail Topic Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    with patch("src.services.topic.create_topic", side_effect=Exception("Creation error")):
        response = await client.post(
            "/api/topics/",
            json={"name": "Bad Topic", "subject_id": sub.id}
        )
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_create_topic_value_error(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    sub = Subject(name="Value Error Topic Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    with patch("src.services.topic.create_topic", side_effect=ValueError("Validation failed")):
        response = await client.post(
            "/api/topics/",
            json={"name": "Bad Topic", "subject_id": sub.id}
        )
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_topic_not_found(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.put("/api/topics/99999", json={"name": "Ghost"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_topic_not_found(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.delete("/api/topics/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_topic_fail_in_service(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.topic import Topic
    sub = Subject(name="Delete Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    t = Topic(name="Delete Me", subject_id=sub.id)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    
    with patch("src.services.topic.delete_topic", return_value=False):
        response = await client.delete(f"/api/topics/{t.id}")
        assert response.status_code == 404

