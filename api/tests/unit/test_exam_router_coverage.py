"""
Tests targeting uncovered lines in src/routers/exam.py:
160, 253, 255, 323, 354, 388, 399, 572-591, 608, 611-613, 625-648, 665, 668-670, 683-687, 698-716, 729, 769-771, 785-813
"""
import pytest
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock
from src.core.deps import get_current_user_info
from src.main import app
from src.models.exam_config import ExamConfig, GenerationStatus, ExamState
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.exam import Exam
from src.models.warning import Warning, WarningType
from src.models.user import User


# ── helpers ──────────────────────────────────────────────────────────────────

def _professor_user(groups=None):
    return User(
        user_id="prof-id",
        username="prof",
        email="prof@test.com",
        realm_roles=["professor"],
        groups=groups or ["/s1/regent", "/w1/regent"],
    )


def _non_professor_user():
    return User(
        user_id="student-id",
        username="student",
        email="student@test.com",
        realm_roles=["student"],
        groups=[],
    )


# ── /generate error paths (lines ~160, 253, 255) ─────────────────────────────

@pytest.mark.asyncio
async def test_generate_missing_subject_id(client, mock_auth, session):
    """Line 160 – 400 when subject_id missing."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/generate", json={"fraction": 0})
    assert response.status_code == 400
    assert "subject_id" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_value_error(client, mock_auth, session):
    """Line 253 – 400 when service raises ValueError."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    with patch("src.routers.exam.create_configs_and_exams", new_callable=AsyncMock,
               side_effect=ValueError("bad value")):
        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "topics": [],
            "number_questions": {},
            "relative_quotations": {},
        }
        response = await client.post("/api/exams/generate", json=payload)
    assert response.status_code == 400
    assert "bad value" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_generic_exception(client, mock_auth, session):
    """Line 255 – 500 when service raises unexpected exception."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="S2")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    with patch("src.routers.exam.create_configs_and_exams", new_callable=AsyncMock,
               side_effect=RuntimeError("boom")):
        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "topics": [],
            "number_questions": {},
            "relative_quotations": {},
        }
        response = await client.post("/api/exams/generate", json=payload)
    assert response.status_code == 500


# ── /generate_async error paths (lines ~323, 354) ────────────────────────────

@pytest.mark.asyncio
async def test_generate_async_missing_subject_id(client, mock_auth, session):
    """Line 323 – 400 when subject_id missing in async endpoint."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/generate_async", json={"fraction": 0})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_generate_async_value_error(client, mock_auth, session):
    """Line 354 – 422 when create_configs raises ValueError."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="S3")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    with patch("src.routers.exam.create_configs", new_callable=AsyncMock,
               side_effect=ValueError("invalid")):
        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "topics": [],
            "number_questions": {},
            "relative_quotations": {},
        }
        response = await client.post("/api/exams/generate_async", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_async_generic_exception(client, mock_auth, session):
    """Line 354 – 500 when create_configs raises unexpected exception."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="S4")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    with patch("src.routers.exam.create_configs", new_callable=AsyncMock,
               side_effect=RuntimeError("crash")):
        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "topics": [],
            "number_questions": {},
            "relative_quotations": {},
        }
        response = await client.post("/api/exams/generate_async", json=payload)
    assert response.status_code == 500


# ── /config/{id}/download error paths (lines ~388, 399) ──────────────────────

@pytest.mark.asyncio
async def test_download_not_found(client, mock_auth, session):
    """Line 388 – 404 when config not found."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/config/99999/download")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_not_completed(client, mock_auth, session):
    """Line 399 – 400 when generation not completed."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="DL Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, status=GenerationStatus.PENDING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    response = await client.get(f"/api/exams/config/{ec.id}/download")
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_download_zip_missing_on_disk(client, mock_auth, session):
    """404 when zip_path is set but file doesn't exist on disk."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="DL Sub2")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(
        subject_id=sub.id, fraction=0,
        status=GenerationStatus.COMPLETED,
        zip_path="/nonexistent/path.zip"
    )
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    response = await client.get(f"/api/exams/config/{ec.id}/download")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ── /config/{id} DELETE error paths (lines ~572-591) ─────────────────────────

@pytest.mark.asyncio
async def test_delete_config_not_found(client, mock_auth, session):
    """404 when config doesn't exist."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.delete("/api/exams/config/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_config_not_in_preparation(client, mock_auth, session):
    """400 when session is not in PREPARING state."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Del Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(
        subject_id=sub.id, fraction=0,
        state=ExamState.RUNNING
    )
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    response = await client.delete(f"/api/exams/config/{ec.id}")
    assert response.status_code == 400
    assert "preparation" in response.json()["detail"].lower()


# ── session/start error paths (lines ~608, 611-613) ──────────────────────────

@pytest.mark.asyncio
async def test_start_session_not_found(client, mock_auth, session):
    """404 when config not found."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.patch("/api/exams/99999/session/start")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_session_not_in_preparation(client, mock_auth, session):
    """400 when session is not in PREPARING state."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Start Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    response = await client.patch(f"/api/exams/{ec.id}/session/start")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_start_session_service_exception(client, mock_auth, session):
    """500 when transition_exam_config_state raises."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Start Sub2")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.PREPARING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    with patch("src.routers.exam.transition_exam_config_state", new_callable=AsyncMock,
               side_effect=RuntimeError("db error")):
        response = await client.patch(f"/api/exams/{ec.id}/session/start")
    assert response.status_code == 500


# ── session/info error paths (lines ~625-648) ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_session_info_not_found(client, session):
    """404 when get_exam_session_info_service returns None."""
    user = _professor_user(groups=["/w99999/regent"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.get_exam_session_info_service", new_callable=AsyncMock,
               return_value=None):
        response = await client.get("/api/exams/99999/session/info")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_info_service_exception(client, session):
    """500 when service raises unexpected exception."""
    user = _professor_user(groups=["/w1/regent"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.get_exam_session_info_service", new_callable=AsyncMock,
               side_effect=RuntimeError("crash")):
        response = await client.get("/api/exams/1/session/info")
    assert response.status_code == 500


# ── session/student_to_exam error paths (lines ~665, 668-670) ────────────────

@pytest.mark.asyncio
async def test_associate_student_config_not_found(client, session):
    """404 when config not found."""
    user = _professor_user(groups=["/w99999/vigilant"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    response = await client.post(
        "/api/exams/99999/session/student_to_exam",
        json={"qr": "1", "nmec": "12345"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_associate_student_session_not_running(client, session):
    """400 when session is not RUNNING."""
    sub = Subject(name="Assoc Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.PREPARING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    user = _professor_user(groups=[f"/w{ec.id}/vigilant"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    response = await client.post(
        f"/api/exams/{ec.id}/session/student_to_exam",
        json={"qr": "1", "nmec": "12345"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_associate_student_invalid_qr(client, session):
    """422 when qr is not a valid integer."""
    sub = Subject(name="Assoc Sub2")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    user = _professor_user(groups=[f"/w{ec.id}/vigilant"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    response = await client.post(
        f"/api/exams/{ec.id}/session/student_to_exam",
        json={"qr": "not-an-int", "nmec": "12345"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_associate_student_service_exception(client, session):
    """500 when associate_student_to_exam_service raises."""
    sub = Subject(name="Assoc Sub3")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    user = _professor_user(groups=[f"/w{ec.id}/vigilant"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.associate_student_to_exam_service", new_callable=AsyncMock,
               side_effect=RuntimeError("db error")):
        response = await client.post(
            f"/api/exams/{ec.id}/session/student_to_exam",
            json={"qr": "1", "nmec": "12345"}
        )
    assert response.status_code == 500


# ── session/metrics error paths (lines ~683-687) ─────────────────────────────

@pytest.mark.asyncio
async def test_get_metrics_not_found(client, session):
    """404 when metrics service returns None."""
    user = _professor_user(groups=["/w99999/regent"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.get_exam_session_metrics_service", new_callable=AsyncMock,
               return_value=None):
        response = await client.get("/api/exams/99999/session/metrics")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_metrics_service_exception(client, session):
    """500 when metrics service raises."""
    user = _professor_user(groups=["/w1/regent"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.get_exam_session_metrics_service", new_callable=AsyncMock,
               side_effect=RuntimeError("crash")):
        response = await client.get("/api/exams/1/session/metrics")
    assert response.status_code == 500


# ── /professor/my-exam-sessions (lines ~698-716) ─────────────────────────────

@pytest.mark.asyncio
async def test_professor_sessions_forbidden_for_non_professor(client, session):
    """403 when user is not a professor."""
    user = _non_professor_user()
    app.dependency_overrides[get_current_user_info] = lambda: user

    response = await client.get("/api/exams/professor/my-exam-sessions")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_professor_sessions_success(client, session):
    """200 with list of sessions for a professor."""
    user = _professor_user(groups=["/w1/regent"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.get_professor_exam_sessions", new_callable=AsyncMock,
               return_value=[]):
        response = await client.get("/api/exams/professor/my-exam-sessions")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_professor_sessions_service_exception(client, session):
    """500 when service raises."""
    user = _professor_user(groups=["/w1/regent"])
    app.dependency_overrides[get_current_user_info] = lambda: user

    with patch("src.routers.exam.get_professor_exam_sessions", new_callable=AsyncMock,
               side_effect=RuntimeError("crash")):
        response = await client.get("/api/exams/professor/my-exam-sessions")
    assert response.status_code == 500


# ── session/close error paths (line ~729) ────────────────────────────────────

@pytest.mark.asyncio
async def test_close_session_not_found(client, mock_auth, session):
    """404 when config not found."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.patch("/api/exams/99999/session/close")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_close_session_value_error(client, mock_auth, session):
    """400 when service raises ValueError."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Close Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    with patch("src.routers.exam.close_exam_session_service", new_callable=AsyncMock,
               side_effect=ValueError("bad state")):
        response = await client.patch(f"/api/exams/{ec.id}/session/close")
    assert response.status_code == 400
    assert "bad state" in response.json()["detail"]


@pytest.mark.asyncio
async def test_close_session_generic_exception(client, mock_auth, session):
    """500 when service raises unexpected exception."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Close Sub2")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    with patch("src.routers.exam.close_exam_session_service", new_callable=AsyncMock,
               side_effect=RuntimeError("crash")):
        response = await client.patch(f"/api/exams/{ec.id}/session/close")
    assert response.status_code == 500


# ── session/notify-students error paths (lines ~769-771, 785-813) ────────────

@pytest.mark.asyncio
async def test_notify_students_config_not_found(client, mock_auth, session):
    """404 when config not found."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post(
        "/api/exams/99999/session/notify-students",
        json={"exam_capture": True, "question_weights": True,
              "red_green_cross_table": True, "cumulative_score_table": True}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_notify_students_session_not_closed(client, mock_auth, session):
    """400 when session is not COMPLETED."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Notify Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    response = await client.post(
        f"/api/exams/{ec.id}/session/notify-students",
        json={"exam_capture": True, "question_weights": True,
              "red_green_cross_table": True, "cumulative_score_table": True}
    )
    assert response.status_code == 400
    assert "closed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_notify_students_unresolved_warnings(client, mock_auth, session):
    """400 when there are unresolved warnings."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Notify Sub2")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.COMPLETED)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    w = Warning(exam_config_id=ec.id, type=WarningType.multiple_students_to_exam)
    session.add(w)
    await session.commit()

    response = await client.post(
        f"/api/exams/{ec.id}/session/notify-students",
        json={"exam_capture": True, "question_weights": True,
              "red_green_cross_table": True, "cumulative_score_table": True}
    )
    assert response.status_code == 400
    assert "warnings" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_notify_students_exam_not_ready(client, mock_auth, session):
    """400 when an exam is not ready (no grade/capture/validated)."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Notify Sub3")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.COMPLETED)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    # Exam with email/nmec but not validated
    e = Exam(
        exam_config_id=ec.id,
        student_email="s@test.com",
        nmec="111",
        grade=None,
        capture_path=None,
        validated=False
    )
    session.add(e)
    await session.commit()

    response = await client.post(
        f"/api/exams/{ec.id}/session/notify-students",
        json={"exam_capture": True, "question_weights": True,
              "red_green_cross_table": True, "cumulative_score_table": True}
    )
    assert response.status_code == 400
    assert "not ready" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_notify_students_success(client, mock_auth, session):
    """200 when all exams are ready and notify_student succeeds."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Notify Sub4")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.COMPLETED)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    e = Exam(
        exam_config_id=ec.id,
        student_email="s@test.com",
        nmec="222",
        grade=15.0,
        capture_path="/some/path.jpg",
        validated=True
    )
    session.add(e)
    await session.commit()

    with patch("src.routers.exam.notify_student", new_callable=AsyncMock, return_value=None):
        response = await client.post(
            f"/api/exams/{ec.id}/session/notify-students",
            json={"exam_capture": True, "question_weights": True,
                  "red_green_cross_table": True, "cumulative_score_table": True}
        )
    assert response.status_code == 200
    assert "completed" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_notify_students_skips_exam_without_email(client, mock_auth, session):
    """200 – exams without email/nmec are silently skipped."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Notify Sub5")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    ec = ExamConfig(subject_id=sub.id, fraction=0, state=ExamState.COMPLETED)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)

    # Exam without email – should be skipped
    e = Exam(exam_config_id=ec.id, student_email=None, nmec=None)
    session.add(e)
    await session.commit()

    with patch("src.routers.exam.notify_student", new_callable=AsyncMock) as mock_notify:
        response = await client.post(
            f"/api/exams/{ec.id}/session/notify-students",
            json={"exam_capture": False, "question_weights": False,
                  "red_green_cross_table": False, "cumulative_score_table": False}
        )
    assert response.status_code == 200
    mock_notify.assert_not_called()
