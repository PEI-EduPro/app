import pytest
import json
from unittest.mock import AsyncMock, patch
from src.core.deps import get_current_user_info
from src.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _setup_subject(session):
    from src.models.subject import Subject
    sub = Subject(name="Test Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


async def _setup_exam_config(session, subject_id, fraction=25.0):
    from src.models.exam_config import ExamConfig, ExamState
    ec = ExamConfig(subject_id=subject_id, fraction=fraction, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)
    return ec


async def _setup_exam(session, exam_config_id):
    from src.models.exam import Exam
    # answer_key: question 0 -> option B (index 1), question 1 -> option A (index 0)
    e = Exam(
        exam_config_id=exam_config_id,
        nmec=12345,
        batch_number=1,
        answer_key={0: 1, 1: 0},
        relative_weights={0: 1.0, 1: 1.0},
    )
    session.add(e)
    await session.commit()
    await session.refresh(e)
    return e


VALID_GRID = {
    "0": {"A": False, "B": True,  "C": False, "D": False},
    "1": {"A": True,  "B": False, "C": False, "D": False},
}

BODY = {
    "testId": 1,
    "grade": 0.0,  # should be ignored
    "grid": VALID_GRID,
}


# ---------------------------------------------------------------------------
# Service unit tests — correct_by_hand()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_correct_by_hand_service_all_correct(session):
    from src.services.exam import correct_by_hand

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=0.0)
    e = await _setup_exam(session, ec.id)

    updated = await correct_by_hand(session, e.id, VALID_GRID)

    assert updated.grade == pytest.approx(20.0)
    assert updated.validated is True
    results = json.loads(updated.results)
    assert results["0"]["B"] is True
    assert results["1"]["A"] is True


@pytest.mark.asyncio
async def test_correct_by_hand_service_all_wrong(session):
    from src.services.exam import correct_by_hand

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=25.0)
    e = await _setup_exam(session, ec.id)

    all_wrong_grid = {
        "0": {"A": True,  "B": False, "C": False, "D": False},  # wrong (correct is B)
        "1": {"A": False, "B": True,  "C": False, "D": False},  # wrong (correct is A)
    }

    updated = await correct_by_hand(session, e.id, all_wrong_grid)

    # Each question is worth 10pts, penalty = 10 * 0.25 = 2.5 per wrong → score floored at 0
    assert updated.grade == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_correct_by_hand_service_grade_floored_at_zero(session):
    from src.services.exam import correct_by_hand

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=100.0)
    e = await _setup_exam(session, ec.id)

    all_wrong_grid = {
        "0": {"A": True,  "B": False, "C": False, "D": False},
        "1": {"A": False, "B": True,  "C": False, "D": False},
    }

    updated = await correct_by_hand(session, e.id, all_wrong_grid)
    assert updated.grade >= 0.0


@pytest.mark.asyncio
async def test_correct_by_hand_service_lowercase_keys(session):
    """Grid keys sent as lowercase letters should be normalised."""
    from src.services.exam import correct_by_hand

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=0.0)
    e = await _setup_exam(session, ec.id)

    lowercase_grid = {
        "0": {"a": False, "b": True,  "c": False, "d": False},
        "1": {"a": True,  "b": False, "c": False, "d": False},
    }

    updated = await correct_by_hand(session, e.id, lowercase_grid)
    assert updated.grade == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_correct_by_hand_service_exam_not_found(session):
    from src.services.exam import correct_by_hand

    with pytest.raises(ValueError, match="Exam not found"):
        await correct_by_hand(session, 99999, VALID_GRID)


@pytest.mark.asyncio
async def test_correct_by_hand_service_persists_results(session):
    from src.services.exam import correct_by_hand

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=0.0)
    e = await _setup_exam(session, ec.id)

    await correct_by_hand(session, e.id, VALID_GRID)

    await session.refresh(e)
    assert e.results is not None
    assert e.grade is not None


# ---------------------------------------------------------------------------
# Endpoint tests — POST /api/exams/{exam_id}/correct_by_hand_job
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_correct_by_hand_endpoint_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/99999/correct_by_hand_job", json=BODY)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_correct_by_hand_endpoint_success(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=0.0)
    e = await _setup_exam(session, ec.id)

    response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json=BODY)

    assert response.status_code == 200
    data = response.json()
    assert data["exam_id"] == e.id
    assert data["grade"] == pytest.approx(20.0)
    assert len(data["questions"]) == 2


@pytest.mark.asyncio
async def test_correct_by_hand_endpoint_grade_ignored(client, mock_auth, session):
    """The grade field from the request body must be ignored."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=0.0)
    e = await _setup_exam(session, ec.id)

    body_with_fake_grade = {**BODY, "grade": 99.9}
    response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json=body_with_fake_grade)

    assert response.status_code == 200
    assert response.json()["grade"] != 99.9


@pytest.mark.asyncio
async def test_correct_by_hand_endpoint_updates_db(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, fraction=0.0)
    e = await _setup_exam(session, ec.id)

    assert e.grade is None
    assert e.results is None

    await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json=BODY)

    await session.refresh(e)
    assert e.grade is not None
    assert e.results is not None
    assert e.validated is True
