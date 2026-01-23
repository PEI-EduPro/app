import pytest
from src.core.deps import get_current_user_info
from src.main import app

@pytest.mark.asyncio
async def test_create_subject(client, mock_auth, mock_keycloak, mock_verify_regent):
    # Override auth to be a manager
    app.dependency_overrides[get_current_user_info] = mock_auth
    # Note: mock_verify_regent is now automatically applied via the fixture (it's a patch)

    response = await client.post(
        "/api/subjects/",
        json={"name": "Test Subject", "regent_keycloak_id": "regent-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Subject"
    assert data["regent_username"] == "regent_user"
    assert "id" in data

    # Verify Keycloak mock was called
    mock_keycloak.create_subject_groups_and_assign_regent.assert_called_once()

@pytest.mark.asyncio
async def test_get_subjects(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    # Pre-populate DB
    from src.models.subject import Subject
    session.add(Subject(name="Math"))
    session.add(Subject(name="Physics"))
    await session.commit()

    response = await client.get("/api/subjects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [s["name"] for s in data]
    assert "Math" in names
    assert "Physics" in names

@pytest.mark.asyncio
async def test_update_subject(client, mock_auth, mock_keycloak, mock_verify_regent, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    from src.models.subject import Subject
    subject = Subject(name="Old Name")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    response = await client.put(
        f"/api/subjects/{subject.id}",
        json={"name": "New Name", "regent_keycloak_id": "new-regent-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    
    # Verify Keycloak update was called
    mock_keycloak.update_subject_regent.assert_called_once_with(
        subject_id=str(subject.id),
        new_regent_id="new-regent-123"
    )

@pytest.mark.asyncio
async def test_delete_subject(client, mock_auth, mock_keycloak, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    from src.models.subject import Subject
    subject = Subject(name="To Delete")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    response = await client.delete(f"/api/subjects/{subject.id}")
    assert response.status_code == 204
    
    # Verify DB
    deleted = await session.get(Subject, subject.id)
    assert deleted is None
    
    # Verify Keycloak delete was called
    mock_keycloak.delete_subject_groups.assert_called_once_with(str(subject.id))