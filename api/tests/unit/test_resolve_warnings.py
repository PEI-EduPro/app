import pytest
import json
from src.core.deps import get_current_user_info
from src.main import app
from src.models.user import User
from src.models.warning import Warning, WarningType
from src.models.subject import Subject
from src.models.exam_config import ExamConfig, ExamState
from src.models.exam import Exam


@pytest.fixture
def regent_user():
    return User(
        user_id="regent-123",
        username="regent",
        email="regent@example.com",
        realm_roles=[],
        groups=["/s1/regent"]
    )


@pytest.fixture
def mock_auth(regent_user):
    async def override():
        return regent_user
    return override


@pytest.fixture
async def setup_data(session):
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    nmec_dict = {
        "111": {"name": "Alice", "email": "alice@example.com"},
        "222": {"name": "Bob", "email": "bob@example.com"},
        "333": {"name": "Carol", "email": "carol@example.com"},
    }
    exam_config = ExamConfig(subject_id=subject.id, fraction=0, nmec_name_list=json.dumps(nmec_dict), state=ExamState.WARNING_HANDLING)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    exam1 = Exam(exam_config_id=exam_config.id, batch_number=1)
    exam2 = Exam(exam_config_id=exam_config.id, batch_number=2)
    exam3 = Exam(exam_config_id=exam_config.id, batch_number=3)
    session.add_all([exam1, exam2, exam3])
    await session.commit()
    await session.refresh(exam1)
    await session.refresh(exam2)
    await session.refresh(exam3)

    return {
        "subject_id": subject.id,
        "exam_config_id": exam_config.id,
        "exam_ids": [exam1.id, exam2.id, exam3.id],
    }


async def _update_associations(session, exam_config_id, associations):
    ec = await session.get(ExamConfig, exam_config_id)
    ec.associations = associations
    session.add(ec)
    await session.commit()
    await session.refresh(ec)
    return ec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url(exam_config_id):
    return f"/api/warnings/{exam_config_id}/resolve"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_clears_multiple_students_to_exam_warning(client, mock_auth, setup_data, session):
    """Assigning one student to a contested exam removes that warning."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    d = setup_data
    exam_id = d["exam_ids"][0]

    # exam1 was scanned with both student 111 and 222 → multiple_students_to_exam
    await _update_associations(session, d["exam_config_id"], [
        f"{exam_id}:111",
        f"{exam_id}:222",
    ])
    session.add(Warning(
        exam_config_id=d["exam_config_id"],
        type=WarningType.multiple_students_to_exam,
        student_list="111:Alice; 222:Bob",
        exam_list=[exam_id],
    ))
    await session.commit()

    response = await client.post(_url(d["exam_config_id"]), json={
        "assignments": [{"exam_id": exam_id, "student_nmec": "111"}]
    })

    assert response.status_code == 200
    assert response.json() == []  # no remaining warnings


@pytest.mark.asyncio
async def test_resolve_clears_multiple_exams_to_student_warning(client, mock_auth, setup_data, session):
    """Reassigning one of the duplicate exams to a different student removes the warning."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    d = setup_data
    exam1_id, exam2_id = d["exam_ids"][0], d["exam_ids"][1]

    # student 111 was assigned to both exam1 and exam2
    await _update_associations(session, d["exam_config_id"], [
        f"{exam1_id}:111",
        f"{exam2_id}:111",
    ])
    session.add(Warning(
        exam_config_id=d["exam_config_id"],
        type=WarningType.multiple_exams_to_student,
        student_list="111:Alice",
        exam_list=[exam1_id, exam2_id],
    ))
    await session.commit()

    # Fix: assign exam2 to student 222 instead
    response = await client.post(_url(d["exam_config_id"]), json={
        "assignments": [{"exam_id": exam2_id, "student_nmec": "222"}]
    })

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_partial_resolve_leaves_remaining_warnings(client, mock_auth, setup_data, session):
    """A batch that only fixes some conflicts should leave the rest as warnings."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    d = setup_data
    exam1_id, exam2_id, exam3_id = d["exam_ids"][0], d["exam_ids"][1], d["exam_ids"][2]

    # exam1: contested by 111 and 222  ← will be resolved
    # exam2: contested by 333 and 111  ← left unresolved (different students from exam1)
    # exam3: clean → 333 only (but 333 is also on exam2, so exam3 stays conflicted too)
    # Use completely disjoint student sets so resolving exam1 has no side effects on exam2
    # exam1: 111 vs 222  — resolve to 111
    # exam2: 333 vs 222  — left alone
    await _update_associations(session, d["exam_config_id"], [
        f"{exam1_id}:111",
        f"{exam1_id}:222",
        f"{exam2_id}:333",
        f"{exam2_id}:222",
    ])
    await session.commit()

    # Only resolve exam1 → 111; exam2 conflict (333 vs 222) remains
    response = await client.post(_url(d["exam_config_id"]), json={
        "assignments": [{"exam_id": exam1_id, "student_nmec": "111"}]
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    remaining_exam_ids = {w["exam_id"] for w in data}
    assert exam2_id in remaining_exam_ids
    assert exam1_id not in remaining_exam_ids


@pytest.mark.asyncio
async def test_resolve_updates_exam_nmec_for_clean_assignments(client, mock_auth, setup_data, session):
    """After resolving, exam.nmec should be set for conflict-free assignments."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    d = setup_data
    exam1_id, exam2_id = d["exam_ids"][0], d["exam_ids"][1]

    await _update_associations(session, d["exam_config_id"], [
        f"{exam1_id}:111",
        f"{exam2_id}:111",  # conflict: student 111 on two exams
    ])
    await session.commit()

    # Fix exam2 → student 222, making both clean
    response = await client.post(_url(d["exam_config_id"]), json={
        "assignments": [{"exam_id": exam2_id, "student_nmec": "222"}]
    })

    assert response.status_code == 200
    assert response.json() == []

    await session.refresh(await session.get(Exam, exam1_id))
    await session.refresh(await session.get(Exam, exam2_id))
    exam1 = await session.get(Exam, exam1_id)
    exam2 = await session.get(Exam, exam2_id)
    assert exam1.nmec == 111
    assert exam2.nmec == 222


@pytest.mark.asyncio
async def test_resolve_replaces_previous_assignment_for_same_exam(client, mock_auth, setup_data, session):
    """Sending a new assignment for an exam that already had one replaces it."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    d = setup_data
    exam1_id = d["exam_ids"][0]

    await _update_associations(session, d["exam_config_id"], [
        f"{exam1_id}:111",
        f"{exam1_id}:222",  # conflict
    ])
    await session.commit()

    # First resolve: pick 111
    await client.post(_url(d["exam_config_id"]), json={
        "assignments": [{"exam_id": exam1_id, "student_nmec": "111"}]
    })

    # Second resolve: change mind, pick 222
    response = await client.post(_url(d["exam_config_id"]), json={
        "assignments": [{"exam_id": exam1_id, "student_nmec": "222"}]
    })

    assert response.status_code == 200
    assert response.json() == []

    # Verify state transition to COMPLETED
    ec = await session.get(ExamConfig, d["exam_config_id"])
    await session.refresh(ec)
    assert ec.state == ExamState.COMPLETED

    exam1 = await session.get(Exam, exam1_id)
    assert exam1.nmec == 222


@pytest.mark.asyncio
async def test_resolve_returns_404_when_no_config(client, mock_auth, setup_data, session):
    """Should return 404 when no exam config exists."""
    app.dependency_overrides[get_current_user_info] = mock_auth
    d = setup_data

    response = await client.post("/api/warnings/9999/resolve", json={
        "assignments": [{"exam_id": d["exam_ids"][0], "student_nmec": "111"}]
    })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_resolve_forbidden_for_non_regent(client, setup_data, session):
    """A user without regent role on the subject should get 403."""
    async def non_regent():
        return User(
            user_id="student-1",
            username="student",
            email="student@example.com",
            realm_roles=[],
            groups=[],
        )
    app.dependency_overrides[get_current_user_info] = non_regent
    d = setup_data

    response = await client.post(_url(d["exam_config_id"]), json={"assignments": []})
    assert response.status_code == 403
