import pytest
from src.core.deps import get_current_user_info
from src.main import app
from src.models.user import User
from src.models.waiting_room import WaitingRoomState, WaitingRoom
from src.models.warning import Warning, WarningType
from src.models.subject import Subject
from src.models.exam_config import ExamConfig
from src.models.exam import Exam
from unittest.mock import AsyncMock, patch
import json

@pytest.fixture
def test_user():
    return User(
        user_id="test-regent-123",
        username="test_regent",
        email="regent@example.com",
        realm_roles=[],
        groups=["/s1/regent", "/w1/regent", "/w99999/regent"]
    )

@pytest.fixture
def mock_auth_user(test_user):
    async def override_get_current_user_info():
        return test_user
    return override_get_current_user_info

@pytest.fixture
async def setup_data(session):
    subject = Subject(name="Test Subject WR")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    # nmec_name_list now expects dict with name and email for each student
    nmec_dict = {
        "12345": {"name": "John Doe", "email": "john@example.com"},
        "67890": {"name": "Jane Doe", "email": "jane@example.com"}
    }
    exam_config = ExamConfig(subject_id=subject.id, fraction=0, nmec_name_list=json.dumps(nmec_dict))
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    exam1 = Exam(exam_config_id=exam_config.id)
    exam2 = Exam(exam_config_id=exam_config.id)
    session.add(exam1)
    session.add(exam2)
    await session.commit()
    await session.refresh(exam1)
    await session.refresh(exam2)

    return {
        "subject_id": subject.id,
        "exam_config_id": exam_config.id,
        "exam_ids": [exam1.id, exam2.id]
    }

@pytest.mark.asyncio
async def test_create_waiting_room(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    
    with patch("src.services.waiting_room.keycloak_client.create_waiting_room_groups", new_callable=AsyncMock) as mock_kc:
        mock_kc.return_value = True
        
        response = await client.post(
            "/api/waiting-rooms/",
            json={"exam_config_id": exam_config_id, "vigilant_keycloak_ids": ["v1", "v2"]}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["exam_config_id"] == exam_config_id
        assert data["state"] == WaitingRoomState.PREPARATION
        assert "id" in data
        mock_kc.assert_called_once()
        
        waiting_room = await session.get(WaitingRoom, data["id"])
        assert waiting_room is not None

@pytest.mark.asyncio
async def test_start_waiting_room(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.patch(f"/api/waiting-rooms/{waiting_room.id}/start")
    
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == WaitingRoomState.RUNNING

@pytest.mark.asyncio
async def test_associate_student_to_exam(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id, state=WaitingRoomState.RUNNING)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.post(
        f"/api/waiting-rooms/{waiting_room.id}/student_to_exam",
        json={"qr": str(exam_ids[0]), "nmec": 12345}
    )
    
    assert response.status_code == 200
    
    updated_room = await session.get(WaitingRoom, waiting_room.id)
    assert f"{exam_ids[0]}:12345" in updated_room.associations

@pytest.mark.asyncio
async def test_get_waiting_room_metrics(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id, state=WaitingRoomState.RUNNING)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.get(f"/api/waiting-rooms/{waiting_room.id}/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert "associated_exams_count" in data
    assert "associated_students_count" in data

@pytest.mark.asyncio
async def test_get_waiting_room_info(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id, state=WaitingRoomState.RUNNING)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.get(f"/api/waiting-rooms/{waiting_room.id}/info")
    
    assert response.status_code == 200
    data = response.json()
    assert "waiting_room_id" in data
    assert "state" in data
    assert "exam_config" in data

@pytest.mark.asyncio
async def test_get_waiting_room_metrics(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]
    
    waiting_room = WaitingRoom(
        exam_config_id=exam_config_id, 
        state=WaitingRoomState.RUNNING,
        associations=[f"{exam_ids[0]}:12345", f"{exam_ids[1]}:67890"]
    )
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.get(f"/api/waiting-rooms/{waiting_room.id}/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert data["associated_exams_count"] == 2
    assert data["associated_students_count"] == 2

@pytest.mark.asyncio
async def test_get_waiting_room_info(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]

    waiting_room = WaitingRoom(
        exam_config_id=exam_config_id,
        state=WaitingRoomState.RUNNING,
        associations=[f"{exam_ids[0]}:12345"]
    )
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)

    response = await client.get(f"/api/waiting-rooms/{waiting_room.id}/info")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == WaitingRoomState.RUNNING
    # student_list is now a list of StudentInfo objects with nmec and name
    student_nmecs = [s["nmec"] for s in data["student_list"]]
    assert "12345" in student_nmecs
    assert len(data["exam_ids"]) == 2
    assert data["total_students"] == 2
    assert data["total_exams"] == 2

@pytest.mark.asyncio
async def test_close_waiting_room_success(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]
    
    waiting_room = WaitingRoom(
        exam_config_id=exam_config_id, 
        state=WaitingRoomState.RUNNING,
        associations=[f"{exam_ids[0]}:12345", f"{exam_ids[1]}:67890"]
    )
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.patch(f"/api/waiting-rooms/{waiting_room.id}/close")
    
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == WaitingRoomState.CLOSED
    
    exam1 = await session.get(Exam, exam_ids[0])
    exam2 = await session.get(Exam, exam_ids[1])
    assert exam1.nmec == 12345
    assert exam2.nmec == 67890

@pytest.mark.asyncio
async def test_close_waiting_room_conflict(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]
    
    waiting_room = WaitingRoom(
        exam_config_id=exam_config_id, 
        state=WaitingRoomState.RUNNING,
        associations=[f"{exam_ids[0]}:12345", f"{exam_ids[1]}:12345"] # Conflict: One student, two exams
    )
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.patch(f"/api/waiting-rooms/{waiting_room.id}/close")
    
    assert response.status_code == 200
    
    updated_room = await session.get(WaitingRoom, waiting_room.id)
    assert updated_room.state == WaitingRoomState.CLOSED # Stops at closed

@pytest.mark.asyncio
async def test_student_to_exam_qr_success(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id, state=WaitingRoomState.RUNNING)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.post(
        f"/api/waiting-rooms/{waiting_room.id}/student_to_exam",
        json={"qr": str(exam_ids[0]), "nmec": 12345}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Student associated to exams successfully."

@pytest.mark.asyncio
async def test_student_to_exam_qr_invalid_exam_id(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id, state=WaitingRoomState.RUNNING)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.post(
        f"/api/waiting-rooms/{waiting_room.id}/student_to_exam",
        json={"qr": "invalid_id", "nmec": 12345}
    )
    
    assert response.status_code == 422
    assert "Invalid exam ID format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_student_to_exam_qr_waiting_room_not_running(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]
    
    waiting_room = WaitingRoom(exam_config_id=exam_config_id, state=WaitingRoomState.PREPARATION)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    
    response = await client.post(
        f"/api/waiting-rooms/{waiting_room.id}/student_to_exam",
        json={"qr": str(exam_ids[0]), "nmec": 12345}
    )
    
    assert response.status_code == 400
    assert "Waiting room must be in running state" in response.json()["detail"]

@pytest.mark.asyncio
async def test_student_to_exam_qr_waiting_room_not_found(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_ids = setup_data["exam_ids"]
    
    response = await client.post(
        f"/api/waiting-rooms/99999/student_to_exam",
        json={"qr": str(exam_ids[0]), "nmec": 12345}
    )
    
    assert response.status_code == 404
    assert "Waiting room not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_waiting_room_exception(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    with patch("src.routers.waiting_room.create_waiting_room_service", side_effect=Exception("Fail")):
        response = await client.post("/api/waiting-rooms/", json={"exam_config_id": ec.id, "vigilant_keycloak_ids": []})
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_start_waiting_room_config_not_found(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec_real = ExamConfig(subject_id=sub.id)
    session.add(ec_real)
    await session.commit()

    wr = WaitingRoom(exam_config_id=ec_real.id)
    session.add(wr)
    await session.commit()
    
    # Now simulate config NOT FOUND by patching session.get
    with patch("src.routers.waiting_room.AsyncSession.get", return_value=None):
        response = await client.patch(f"/api/waiting-rooms/{wr.id}/start")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_start_waiting_room_wrong_state(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom, WaitingRoomState
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id, state=WaitingRoomState.RUNNING)
    session.add(wr)
    await session.commit()
    
    response = await client.patch(f"/api/waiting-rooms/{wr.id}/start")
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_get_waiting_room_info_exception(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()

    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    await session.commit()
    
    with patch("src.routers.waiting_room.get_waiting_room_info_service", side_effect=Exception("Fail")):
        response = await client.get(f"/api/waiting-rooms/{wr.id}/info")
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_associate_student_to_exam_value_error(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom, WaitingRoomState
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()

    wr = WaitingRoom(exam_config_id=ec.id, state=WaitingRoomState.RUNNING)
    session.add(wr)
    await session.commit()
    
    response = await client.post(f"/api/waiting-rooms/{wr.id}/student_to_exam", json={"qr": "not-int", "nmec": 123})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_waiting_room_metrics_not_found(client, session):
    # Need user with permission for w9999
    from src.models.user import User
    u = User(user_id="u1", username="u1", email="u1@e.com", realm_roles=[], groups=["/w9999/regent"])
    async def mock_u(): return u
    app.dependency_overrides[get_current_user_info] = mock_u

    with patch("src.routers.waiting_room.get_waiting_room_metrics_service", return_value=None):
        response = await client.get("/api/waiting-rooms/9999/metrics")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_close_waiting_room_config_not_found(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()

    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    await session.commit()
    
    with patch("src.routers.waiting_room.AsyncSession.get", return_value=None):
        response = await client.patch(f"/api/waiting-rooms/{wr.id}/close")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_submitted_exams_count_not_found(client, mock_auth_user):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    response = await client.get("/api/waiting-rooms/9999/submitted_count")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_evaluate_exam_batch_not_found(client, mock_auth_user):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    response = await client.post("/api/waiting-rooms/9999/evaluate", json={"files": []})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_notify_students_via_email_not_found(client, mock_auth_user):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    response = await client.post("/api/waiting-rooms/9999/notify-students", json={"sender_email": "a@b.com", "sender_password": "p", "subject": "s", "body": "b"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_notify_students_via_email_with_warnings(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom, WaitingRoomState
    from src.models.warning import Warning, WarningType
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id, state=WaitingRoomState.CLOSED)
    session.add(wr)
    await session.commit()
    warn = Warning(exam_config_id=ec.id, description="Warn", type=WarningType.multiple_exams_to_student)
    session.add(warn)
    await session.commit()
    
    response = await client.post(f"/api/waiting-rooms/{wr.id}/notify-students", json={"sender_email": "a@b.com", "sender_password": "p", "subject": "s", "body": "b"})
    assert response.status_code == 400
    assert "pending warning" in response.json()["detail"]

@pytest.mark.asyncio
async def test_notify_students_not_corrected(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom, WaitingRoomState
    from src.models.exam import Exam
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id, state=WaitingRoomState.CLOSED)
    session.add(wr)
    await session.commit()
    e = Exam(exam_config_id=ec.id, nmec=123, student_email="s@e.com", student_name="S")
    session.add(e)
    await session.commit()
    
    response = await client.post(f"/api/waiting-rooms/{wr.id}/notify-students", json={"sender_email": "a@b.com", "sender_password": "p", "subject": "s", "body": "b"})
    assert response.status_code == 400
    assert "not yet been corrected" in response.json()["detail"]

@pytest.mark.asyncio
async def test_notify_students_not_validated(client, mock_auth_user, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.waiting_room import WaitingRoom, WaitingRoomState
    from src.models.exam import Exam
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    wr = WaitingRoom(exam_config_id=ec.id, state=WaitingRoomState.CLOSED)
    session.add(wr)
    await session.commit()
    e = Exam(exam_config_id=ec.id, nmec=123, student_email="s@e.com", student_name="S", 
             capture_path="c", correction_path="cr", grade=10, results="{}", validated=False)
    session.add(e)
    await session.commit()
    
    response = await client.post(f"/api/waiting-rooms/{wr.id}/notify-students", json={"sender_email": "a@b.com", "sender_password": "p", "subject": "s", "body": "b"})
    assert response.status_code == 400
    assert "has not been validated" in response.json()["detail"]
