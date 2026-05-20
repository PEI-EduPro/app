import pytest
from src.core.deps import get_current_user_info
from src.main import app
from src.models.user import User
from src.models.warning import Warning, WarningType
from src.models.subject import Subject
from src.models.exam_config import ExamConfig, ExamState
from src.models.exam import Exam
import json

@pytest.fixture
def test_user():
    return User(
        user_id="test-regent-123",
        username="test_regent",
        email="regent@example.com",
        realm_roles=[],
        groups=["/s1/regent"]
    )

@pytest.fixture
def mock_auth_user(test_user):
    async def override_get_current_user_info():
        return test_user
    return override_get_current_user_info

@pytest.fixture
async def setup_data(session):
    subject = Subject(name="Test Subject Warnings")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    nmec_dict = {
        "12345": {"name": "John Doe", "email": "john@example.com"},
        "67890": {"name": "Jane Doe", "email": "jane@example.com"}
    }
    exam_config = ExamConfig(subject_id=subject.id, fraction=0, nmec_name_list=json.dumps(nmec_dict), state=ExamState.WARNING_HANDLING)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    exam1 = Exam(exam_config_id=exam_config.id, batch_number=1)
    exam2 = Exam(exam_config_id=exam_config.id, batch_number=2)
    session.add(exam1)
    session.add(exam2)
    await session.commit()
    await session.refresh(exam1)
    await session.refresh(exam2)

    return {
        "subject_id": subject.id,
        "exam_config_id": exam_config.id,
        "exam_ids": [exam1.id, exam2.id],
    }

@pytest.mark.asyncio
async def test_get_warnings_by_exam_config_id(client, mock_auth_user, setup_data, session):
    app.dependency_overrides[get_current_user_info] = mock_auth_user
    exam_config_id = setup_data["exam_config_id"]
    exam_ids = setup_data["exam_ids"]

    # Insert WarningType.multiple_students_to_exam
    warning1 = Warning(
        exam_config_id=exam_config_id,
        type=WarningType.multiple_students_to_exam,
        student_list="12345:John Doe; 67890:Jane Doe",
        exam_list=[exam_ids[0]]
    )
    # Insert WarningType.multiple_exams_to_student
    warning2 = Warning(
        exam_config_id=exam_config_id,
        type=WarningType.multiple_exams_to_student,
        student_list="12345:John Doe",
        exam_list=[exam_ids[0], exam_ids[1]]
    )
    # Insert WarningType.exam_correction_no_student
    warning3 = Warning(
        exam_config_id=exam_config_id,
        type=WarningType.exam_correction_no_student,
        student_list="",
        exam_list=[exam_ids[1]]
    )

    session.add_all([warning1, warning2, warning3])
    await session.commit()

    response = await client.get(f"/api/warnings/{exam_config_id}")

    assert response.status_code == 200
    data = response.json()
    warnings = data["warnings"]

    # We expect 4 items in the warnings list:
    # 1 for warning1
    # 2 for warning2
    # 1 for warning3
    assert len(warnings) == 4

    # Assert WarningType.multiple_students_to_exam handling
    w1_res = next(w for w in warnings if w["exam_id"] == exam_ids[0] and len(w["students"]) == 2)
    assert w1_res["batch_number"] == 1
    assert w1_res["students"][0]["nmec"] == 12345
    assert w1_res["students"][0]["name"] == "John Doe"
    assert w1_res["students"][1]["nmec"] == 67890
    assert w1_res["students"][1]["name"] == "Jane Doe"

    # Assert WarningType.multiple_exams_to_student handling
    # Should result in two entries for the same student, different exams
    w2_res1 = next(w for w in warnings if w["exam_id"] == exam_ids[0] and len(w["students"]) == 1)
    w2_res2 = next(w for w in warnings if w["exam_id"] == exam_ids[1] and len(w["students"]) == 1)

    assert w2_res1["batch_number"] == 1
    assert w2_res1["students"][0]["nmec"] == 12345

    assert w2_res2["batch_number"] == 2
    assert w2_res2["students"][0]["nmec"] == 12345

    # Assert WarningType.exam_correction_no_student handling
    w3_res = next(w for w in warnings if w["exam_id"] == exam_ids[1] and len(w["students"]) == 0)
    assert w3_res["batch_number"] == 2
    assert w3_res["students"] == []

    # Assert students list: both students are in warnings, so both should appear
    students = data["students"]
    student_nmecs = {s["nmec"] for s in students}
    assert "12345" in student_nmecs
    assert "67890" in student_nmecs

@pytest.mark.asyncio
async def test_get_warnings_unauthorized(client, session, setup_data):
    # We can override with a student or random user
    async def override_unauthorized_user():
        return User(
            user_id="test-student",
            username="student",
            email="student@example.com",
            realm_roles=[],
            groups=[] # Not a regent
        )
    app.dependency_overrides[get_current_user_info] = override_unauthorized_user

    exam_config_id = setup_data["exam_config_id"]
    response = await client.get(f"/api/warnings/{exam_config_id}")

    assert response.status_code == 403
