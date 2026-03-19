import pytest
from src.core.deps import get_current_user_info, verify_regent_exists
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

@pytest.mark.asyncio
async def test_create_subject_unauthorized(client, session):
    # No auth override, or override with non-manager
    # By default client is not authenticated if we don't override get_current_user_info
    # But wait, dependency override is cleared in fixture. 
    # Let's mock a student user
    from src.models.user import User
    student_user = User(user_id="s1", username="stu", email="s@t.com", realm_roles=["student"], groups=[])
    
    async def mock_student():
        return student_user
        
    app.dependency_overrides[get_current_user_info] = mock_student
    
    response = await client.post(
        "/api/subjects/",
        json={"name": "Hacking 101", "regent_keycloak_id": "r1"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_subject_invalid_regent(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    # We need to simulate verify_regent_exists failing
    from fastapi import HTTPException
    
    async def mock_fail_regent(regent_keycloak_id: str):
        raise HTTPException(status_code=400, detail=f"Regent user with ID '{regent_keycloak_id}' not found.")
        
    # Override the patch from conftest
    app.dependency_overrides[verify_regent_exists] = mock_fail_regent
    # Note: If the service imports verify_regent_exists directly, dependency_overrides might not work 
    # if it's not used as a Depends() in the route but called as a function in service.
    # In subject_service, it IS called as a function. 
    # So we must PATCH it, not use dependency_overrides.
    
    from unittest.mock import patch
    with patch("src.services.subject.verify_regent_exists", side_effect=HTTPException(status_code=400, detail="Regent not found")):
        response = await client.post(
            "/api/subjects/",
            json={"name": "Bad Regent Subject", "regent_keycloak_id": "invalid-id"}
        )
        assert response.status_code == 400
        assert "Regent not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_subject_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth

    response = await client.put(
        "/api/subjects/99999",
        json={"name": "Ghost Subject"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_regent_update_students(client, session, mock_keycloak):
    """Test that a regent can update students for their subject."""
    from src.models.user import User
    from src.models.subject import Subject

    # Create a regent user for subject 1
    regent_user = User(
        user_id="regent-id-123",
        username="regent",
        email="regent@example.com",
        realm_roles=["professor"],
        groups=["/s1/regent"]
    )

    async def mock_regent():
        return regent_user

    app.dependency_overrides[get_current_user_info] = mock_regent

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # Regent updates only students (allowed)
    response = await client.put(
        f"/api/subjects/{subject.id}",
        json={"student_keycloak_ids": ["student-1", "student-2"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Subject"
    mock_keycloak.replace_subject_students.assert_called_once_with(
        subject_id=str(subject.id),
        student_ids=["student-1", "student-2"]
    )

@pytest.mark.asyncio
async def test_regent_update_professors(client, session, mock_keycloak):
    """Test that a regent can update professors for their subject."""
    from src.models.user import User
    from src.models.subject import Subject

    regent_user = User(
        user_id="regent-id-123",
        username="regent",
        email="regent@example.com",
        realm_roles=["professor"],
        groups=["/s1/regent"]
    )

    async def mock_regent():
        return regent_user

    app.dependency_overrides[get_current_user_info] = mock_regent

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # Regent updates only professors (allowed)
    response = await client.put(
        f"/api/subjects/{subject.id}",
        json={"professor_keycloak_ids": ["prof-1", "prof-2"]}
    )

    assert response.status_code == 200
    mock_keycloak.replace_subject_professors.assert_called_once_with(
        subject_id=str(subject.id),
        professor_ids=["prof-1", "prof-2"]
    )

@pytest.mark.asyncio
async def test_regent_cannot_update_name(client, session):
    """Test that a regent cannot update the subject name."""
    from src.models.user import User
    from src.models.subject import Subject

    regent_user = User(
        user_id="regent-id-123",
        username="regent",
        email="regent@example.com",
        realm_roles=["professor"],
        groups=["/s1/regent"]
    )

    async def mock_regent():
        return regent_user

    app.dependency_overrides[get_current_user_info] = mock_regent

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # Regent tries to update name (forbidden)
    response = await client.put(
        f"/api/subjects/{subject.id}",
        json={"name": "New Name"}
    )

    assert response.status_code == 403
    assert "Only managers can update" in response.json()["detail"]

@pytest.mark.asyncio
async def test_regent_cannot_update_regent(client, session):
    """Test that a regent cannot update the regent."""
    from src.models.user import User
    from src.models.subject import Subject

    regent_user = User(
        user_id="regent-id-123",
        username="regent",
        email="regent@example.com",
        realm_roles=["professor"],
        groups=["/s1/regent"]
    )

    async def mock_regent():
        return regent_user

    app.dependency_overrides[get_current_user_info] = mock_regent

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # Regent tries to update regent (forbidden)
    response = await client.put(
        f"/api/subjects/{subject.id}",
        json={"regent_keycloak_id": "new-regent-456"}
    )

    assert response.status_code == 403
    assert "Only managers can update" in response.json()["detail"]

@pytest.mark.asyncio
async def test_non_regent_cannot_update_subject(client, session):
    """Test that a user who is not a regent or manager cannot update the subject."""
    from src.models.user import User
    from src.models.subject import Subject

    student_user = User(
        user_id="student-id-123",
        username="student",
        email="student@example.com",
        realm_roles=["student"],
        groups=["/s1/student"]
    )

    async def mock_student():
        return student_user

    app.dependency_overrides[get_current_user_info] = mock_student

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    response = await client.put(
        f"/api/subjects/{subject.id}",
        json={"name": "Hacked Name"}
    )

    assert response.status_code == 403
    assert "Only managers or subject regents" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_subject_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    response = await client.delete("/api/subjects/99999")
    assert response.status_code == 404