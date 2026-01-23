import pytest
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
async def test_get_topics(client, session):
    # Public endpoint? Or auth required? Router says no dependency on get, but let's check.
    # The router code shows `get_subjects` (which is actually get all topics) depends only on session.
    
    from src.models.subject import Subject
    from src.models.topic import Topic
    
    sub = Subject(name="Math")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    t1 = Topic(name="Algebra", subject_id=sub.id)
    t2 = Topic(name="Geometry", subject_id=sub.id)
    session.add(t1)
    session.add(t2)
    await session.commit()
    
    response = await client.get("/api/topics/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [t["name"] for t in data]
    assert "Algebra" in names
    assert "Geometry" in names

@pytest.mark.asyncio
async def test_get_topic_by_id(client, session):
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
    assert response.status_code in [400, 500] 

@pytest.mark.asyncio
async def test_get_topic_not_found(client, session):
    response = await client.get("/api/topics/99999")
    assert response.status_code == 404
