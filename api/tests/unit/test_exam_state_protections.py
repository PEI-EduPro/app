import pytest
from src.models.exam_config import ExamState
from src.core.deps import get_current_user_info
from src.main import app

async def _setup_subject(session):
    from src.models.subject import Subject
    sub = Subject(name="Test Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub

async def _setup_exam_config(session, subject_id, state=ExamState.PREPARING):
    from src.models.exam_config import ExamConfig
    ec = ExamConfig(subject_id=subject_id, state=state)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)
    return ec

async def _setup_exam(session, exam_config_id, corrected=False):
    from src.models.exam import Exam
    e = Exam(
        exam_config_id=exam_config_id,
        nmec=12345,
        batch_number=1,
        answer_key={0: 1},
        relative_weights={0: 1.0},
    )
    if corrected:
        e.grade = 10.0
        e.results = '{"0": {"B": true}}'
        e.capture_path = "some/path.png"
    session.add(e)
    await session.commit()
    await session.refresh(e)
    return e

VALID_GRID = {
    "0": {"A": False, "B": True, "C": False, "D": False},
}

@pytest.mark.asyncio
async def test_correct_by_hand_wrong_state(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, state=ExamState.RUNNING)
    e = await _setup_exam(session, ec.id)

    body = {"testId": e.id, "grade": 0.0, "grid": VALID_GRID}
    response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json=body)
    assert response.status_code == 400
    assert "not validation or completed" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_correct_by_hand_validation_state(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, state=ExamState.VALIDATION)
    e = await _setup_exam(session, ec.id)

    body = {"testId": e.id, "grade": 0.0, "grid": VALID_GRID}
    response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json=body)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_correct_by_hand_completed_state(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    sub = await _setup_subject(session)
    ec = await _setup_exam_config(session, sub.id, state=ExamState.COMPLETED)
    e = await _setup_exam(session, ec.id)

    body = {"testId": e.id, "grade": 0.0, "grid": VALID_GRID}
    response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json=body)
    assert response.status_code == 200
