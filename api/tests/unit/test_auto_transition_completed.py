import pytest
from src.main import app
from src.core.deps import get_current_user_info
from src.models.user import User
from src.models.subject import Subject
from src.models.exam_config import ExamConfig, ExamState
from src.models.exam import Exam

def _regent_user():
    return User(
        user_id="regent-id",
        username="regent",
        email="regent@test.com",
        realm_roles=["professor"],
        groups=["/s1/regent"],
    )

@pytest.mark.asyncio
async def test_correct_by_hand_auto_transition_to_completed(client, session):
    # Setup test data
    sub = Subject(id=1, name="Test Subject")
    session.add(sub)
    await session.commit()
    
    # Start in VALIDATION state
    ec = ExamConfig(id=1, subject_id=1, fraction=50, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()
    
    # Two exams with pictures
    e1 = Exam(id=1, exam_config_id=1, grade=10, results="{}", capture_path="p1", validated=False)
    e2 = Exam(id=2, exam_config_id=1, grade=15, results="{}", capture_path="p2", validated=False)
    session.add_all([e1, e2])
    await session.commit()
    
    app.dependency_overrides[get_current_user_info] = _regent_user
    
    # Correct first exam by hand - should NOT transition yet
    response = await client.post("/api/exams/1/correct_by_hand_job", json={"grid": {}})
    assert response.status_code == 200
    await session.refresh(ec)
    assert ec.state == ExamState.VALIDATION
    assert (await session.get(Exam, 1)).validated is True
    
    # Correct second exam by hand - should transition to COMPLETED
    response = await client.post("/api/exams/2/correct_by_hand_job", json={"grid": {}})
    assert response.status_code == 200
    await session.refresh(ec)
    assert ec.state == ExamState.COMPLETED
    assert (await session.get(Exam, 2)).validated is True
    
    app.dependency_overrides.clear()
