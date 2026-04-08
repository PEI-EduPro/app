import pytest
import json
import base64
import io
from unittest.mock import patch, AsyncMock, MagicMock
from src.core.deps import get_current_user_info
from src.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_exam_config(session, subject_id):
    from src.models.exam_config import ExamConfig
    ec = ExamConfig(subject_id=subject_id, fraction=0.0)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)
    return ec


async def _setup_exam(session, exam_config_id, *, corrected=False):
    from src.models.exam import Exam
    e = Exam(
        exam_config_id=exam_config_id,
        nmec=12345,
        batch_number=1,
        answer_key={0: 1},
        relative_weights={0: 1.0},
        grade=18.0 if corrected else None,
        results=json.dumps({"0": {"A": False, "B": True, "C": False, "D": False}}) if corrected else None,
        capture_path="/tmp/exam.jpg" if corrected else None,
    )
    session.add(e)
    await session.commit()
    await session.refresh(e)
    return e


async def _setup_waiting_room(session, exam_config_id, state):
    from src.models.waiting_room import WaitingRoom, WaitingRoomState
    wr = WaitingRoom(exam_config_id=exam_config_id, state=state)
    session.add(wr)
    await session.commit()
    await session.refresh(wr)
    return wr


# ---------------------------------------------------------------------------
# POST /api/waiting-rooms/{waiting_room_id}/evaluate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluate_batch_waiting_room_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/waiting-rooms/9999/evaluate", files=[])
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_evaluate_batch_wrong_state(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.waiting_room import WaitingRoomState

    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    wr = await _setup_waiting_room(session, ec.id, WaitingRoomState.RUNNING)

    dummy_file = ("files", ("exam.jpg", b"fake", "image/jpeg"))
    response = await client.post(f"/api/waiting-rooms/{wr.id}/evaluate", files=[dummy_file])
    assert response.status_code == 400
    assert "closed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_evaluate_batch_exam_wrong_config(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.waiting_room import WaitingRoomState

    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec1 = await _setup_exam_config(session, sub.id)
    ec2 = await _setup_exam_config(session, sub.id)
    wr = await _setup_waiting_room(session, ec1.id, WaitingRoomState.CLOSED)
    exam_wrong = await _setup_exam(session, ec2.id)  # belongs to ec2, not ec1

    with patch("src.routers.waiting_room.utils.read_QR", new_callable=AsyncMock) as mock_qr:
        mock_qr.return_value = (exam_wrong.id, "/tmp/exam.jpg")
        dummy_file = ("files", ("exam.jpg", b"fake", "image/jpeg"))
        response = await client.post(f"/api/waiting-rooms/{wr.id}/evaluate", files=[dummy_file])

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"]


@pytest.mark.asyncio
async def test_evaluate_batch_success(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.waiting_room import WaitingRoomState

    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    wr = await _setup_waiting_room(session, ec.id, WaitingRoomState.CLOSED)
    exam_instance = await _setup_exam(session, ec.id)

    with patch("src.routers.waiting_room.utils.read_QR", new_callable=AsyncMock) as mock_qr, \
         patch("src.routers.waiting_room.evaluate_exam", new_callable=AsyncMock) as mock_eval:
        mock_qr.return_value = (exam_instance.id, "/tmp/exam.jpg")
        mock_eval.return_value = None
        dummy_file = ("files", ("exam.jpg", b"fake", "image/jpeg"))
        response = await client.post(f"/api/waiting-rooms/{wr.id}/evaluate", files=[dummy_file])

    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["exam_id"] == exam_instance.id
    assert results[0]["status"] == "success"


# ---------------------------------------------------------------------------
# POST /api/exams/{exam_id}/validate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_exam_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/9999/validate")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validate_exam_not_corrected(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    e = await _setup_exam(session, ec.id, corrected=False)

    response = await client.post(f"/api/exams/{e.id}/validate")
    assert response.status_code == 400
    assert "not been corrected" in response.json()["detail"]


@pytest.mark.asyncio
async def test_validate_exam_success(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.exam import Exam
    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    e = await _setup_exam(session, ec.id, corrected=True)

    response = await client.post(f"/api/exams/{e.id}/validate")
    assert response.status_code == 200

    await session.refresh(e)
    assert e.validated is True


# ---------------------------------------------------------------------------
# GET /api/exams/{exam_id}/exam_info
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exam_info_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/9999/exam_info")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_exam_info_not_corrected(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    e = await _setup_exam(session, ec.id, corrected=False)

    response = await client.get(f"/api/exams/{e.id}/exam_info")
    assert response.status_code == 200
    data = response.json()
    assert data["corrected"] is False
    assert data["grade"] is None
    assert data["results"] is None
    assert data["capture"] is None


@pytest.mark.asyncio
async def test_exam_info_corrected(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    e = await _setup_exam(session, ec.id, corrected=True)

    # Write a dummy image file so the endpoint can read it
    with open("/tmp/exam.jpg", "wb") as f:
        f.write(b"fakeimagebytes")

    response = await client.get(f"/api/exams/{e.id}/exam_info")
    assert response.status_code == 200
    data = response.json()
    assert data["corrected"] is True
    assert data["grade"] == 18.0
    assert data["results"] is not None
    assert data["capture"] == base64.b64encode(b"fakeimagebytes").decode()


# ---------------------------------------------------------------------------
# GET /api/exams/{exam_config_id}/all_exams_info
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_exams_info_empty(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)

    response = await client.get(f"/api/exams/{ec.id}/all_exams_info")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_all_exams_info_mixed(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    sub = Subject(name="Subj")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = await _setup_exam_config(session, sub.id)
    e_corrected = await _setup_exam(session, ec.id, corrected=True)
    e_uncorrected = await _setup_exam(session, ec.id, corrected=False)

    with open("/tmp/exam.jpg", "wb") as f:
        f.write(b"fakeimagebytes")

    response = await client.get(f"/api/exams/{ec.id}/all_exams_info")
    assert response.status_code == 200
    data = response.json()

    assert str(e_corrected.id) in data
    assert str(e_uncorrected.id) in data
    assert data[str(e_corrected.id)]["corrected"] is True
    assert data[str(e_uncorrected.id)]["corrected"] is False
