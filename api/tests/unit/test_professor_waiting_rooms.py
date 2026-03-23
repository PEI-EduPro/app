import pytest
from src.core.deps import get_current_user_info
from src.main import app
from src.models.user import User
from src.models.waiting_room import WaitingRoom, WaitingRoomState
from src.models.subject import Subject
from src.models.exam_config import ExamConfig


@pytest.fixture
def professor_user():
    """Create a mock professor user with waiting room groups."""
    return User(
        user_id="prof-123",
        username="test_professor",
        email="prof@example.com",
        realm_roles=["professor"],
        groups=[
            "/s1/regent",
            "w1/regent",
            "w2/vigilant",
            "w3/regent"
        ]
    )


@pytest.fixture
def professor_user_no_waiting_rooms():
    """Create a mock professor with no waiting room groups."""
    return User(
        user_id="prof-456",
        username="test_professor_2",
        email="prof2@example.com",
        realm_roles=["professor"],
        groups=["/s1/regent", "/s1/professors"]
    )


@pytest.fixture
def student_user():
    """Create a mock student user (should be denied access)."""
    return User(
        user_id="student-789",
        username="test_student",
        email="student@example.com",
        realm_roles=["student"],
        groups=["/s1/student"]
    )


@pytest.fixture
async def setup_waiting_rooms(session):
    """Create subjects, exam configs, and waiting rooms for testing."""
    # Create subjects
    subject1 = Subject(name="Subject 1")
    subject2 = Subject(name="Subject 2")
    session.add(subject1)
    session.add(subject2)
    await session.commit()
    await session.refresh(subject1)
    await session.refresh(subject2)

    # Create exam configs
    exam_config1 = ExamConfig(subject_id=subject1.id, fraction=0)
    exam_config2 = ExamConfig(subject_id=subject1.id, fraction=1)
    exam_config3 = ExamConfig(subject_id=subject2.id, fraction=0)
    session.add(exam_config1)
    session.add(exam_config2)
    session.add(exam_config3)
    await session.commit()
    await session.refresh(exam_config1)
    await session.refresh(exam_config2)
    await session.refresh(exam_config3)

    # Create waiting rooms with different states
    wr1 = WaitingRoom(exam_config_id=exam_config1.id, state=WaitingRoomState.PREPARATION)
    wr2 = WaitingRoom(exam_config_id=exam_config2.id, state=WaitingRoomState.RUNNING)
    wr3 = WaitingRoom(exam_config_id=exam_config3.id, state=WaitingRoomState.CLOSED)
    session.add(wr1)
    session.add(wr2)
    session.add(wr3)
    await session.commit()
    await session.refresh(wr1)
    await session.refresh(wr2)
    await session.refresh(wr3)

    return {
        "subject1_id": subject1.id,
        "subject2_id": subject2.id,
        "wr1_id": wr1.id,
        "wr2_id": wr2.id,
        "wr3_id": wr3.id
    }


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_success(client, professor_user, setup_waiting_rooms, session):
    """Test professor can retrieve their waiting rooms as a flat list."""
    app.dependency_overrides[get_current_user_info] = lambda: professor_user
    
    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")
    
    assert response.status_code == 200
    waiting_rooms = response.json()
    
    # Should be a list with 3 waiting rooms
    assert isinstance(waiting_rooms, list)
    assert len(waiting_rooms) == 3
    
    # Create a lookup by waiting_room_id for easier assertions
    wr_lookup = {wr["waiting_room_id"]: wr for wr in waiting_rooms}
    
    # Check wr1 (regent, preparation)
    wr1 = wr_lookup[setup_waiting_rooms["wr1_id"]]
    assert wr1["subject_id"] == setup_waiting_rooms["subject1_id"]
    assert wr1["subject_name"] == "Subject 1"
    assert wr1["waiting_room_id"] == setup_waiting_rooms["wr1_id"]
    assert wr1["state"] == "preparation"
    assert wr1["role"] == "regent"
    
    # Check wr2 (vigilant, running)
    wr2 = wr_lookup[setup_waiting_rooms["wr2_id"]]
    assert wr2["subject_id"] == setup_waiting_rooms["subject1_id"]
    assert wr2["subject_name"] == "Subject 1"
    assert wr2["waiting_room_id"] == setup_waiting_rooms["wr2_id"]
    assert wr2["state"] == "running"
    assert wr2["role"] == "vigilant"
    
    # Check wr3 (regent, closed)
    wr3 = wr_lookup[setup_waiting_rooms["wr3_id"]]
    assert wr3["subject_id"] == setup_waiting_rooms["subject2_id"]
    assert wr3["subject_name"] == "Subject 2"
    assert wr3["waiting_room_id"] == setup_waiting_rooms["wr3_id"]
    assert wr3["state"] == "closed"
    assert wr3["role"] == "regent"


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_empty(client, professor_user_no_waiting_rooms, session):
    """Test professor with no waiting room groups gets empty list."""
    app.dependency_overrides[get_current_user_info] = lambda: professor_user_no_waiting_rooms
    
    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")
    
    assert response.status_code == 200
    waiting_rooms = response.json()
    
    assert isinstance(waiting_rooms, list)
    assert len(waiting_rooms) == 0


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_denied_for_student(client, student_user, session):
    """Test that students cannot access the professor waiting rooms endpoint."""
    app.dependency_overrides[get_current_user_info] = lambda: student_user
    
    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")
    
    assert response.status_code == 403
    assert "professor role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_partial_groups(client, session):
    """Test professor with only some waiting room groups."""
    partial_prof = User(
        user_id="prof-partial",
        username="partial_prof",
        email="partial@example.com",
        realm_roles=["professor"],
        groups=["w1/regent"]  # Only one waiting room group
    )
    
    # Create only one waiting room
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=0)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    wr = WaitingRoom(exam_config_id=exam_config.id, state=WaitingRoomState.RUNNING)
    session.add(wr)
    await session.commit()
    await session.refresh(wr)
    
    app.dependency_overrides[get_current_user_info] = lambda: partial_prof
    
    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")
    
    assert response.status_code == 200
    waiting_rooms = response.json()
    
    # Should be a list with one item
    assert isinstance(waiting_rooms, list)
    assert len(waiting_rooms) == 1
    
    wr_data = waiting_rooms[0]
    assert wr_data["subject_id"] == subject.id
    assert wr_data["subject_name"] == "Test Subject"
    assert wr_data["waiting_room_id"] == wr.id
    assert wr_data["state"] == "running"
    assert wr_data["role"] == "regent"


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_invalid_group_format(client, session):
    """Test that invalid group formats are gracefully ignored."""
    prof_with_invalid_groups = User(
        user_id="prof-invalid",
        username="invalid_prof",
        email="invalid@example.com",
        realm_roles=["professor"],
        groups=[
            "w1/regent",      # Valid
            "waiting/123",    # Invalid format
            "wabc/regent",    # Invalid ID
            "w999/vigilant"   # Valid but WR doesn't exist
        ]
    )
    
    # Create one waiting room
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=0)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    wr = WaitingRoom(exam_config_id=exam_config.id, state=WaitingRoomState.PREPARATION)
    session.add(wr)
    await session.commit()
    await session.refresh(wr)
    
    app.dependency_overrides[get_current_user_info] = lambda: prof_with_invalid_groups
    
    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")
    
    assert response.status_code == 200
    waiting_rooms = response.json()
    
    # Should have only the valid waiting room that exists
    assert isinstance(waiting_rooms, list)
    assert len(waiting_rooms) == 1
    assert waiting_rooms[0]["waiting_room_id"] == wr.id


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_non_existent_waiting_room(client, session):
    """Test that non-existent waiting room IDs in groups are handled gracefully."""
    # Professor has group w999/regent but that waiting room doesn't exist in DB
    prof_no_wr = User(
        user_id="prof-no-wr",
        username="prof_no_wr",
        email="nowr@example.com",
        realm_roles=["professor"],
        groups=["w999/regent"]  # References non-existent waiting room
    )
    
    app.dependency_overrides[get_current_user_info] = lambda: prof_no_wr
    
    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")
    
    assert response.status_code == 200
    waiting_rooms = response.json()
    
    # Should return empty list since the waiting room doesn't exist
    assert isinstance(waiting_rooms, list)
    assert len(waiting_rooms) == 0


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_multiple_subjects(client, professor_user, setup_waiting_rooms, session):
    """Test professor with waiting rooms across multiple subjects."""
    app.dependency_overrides[get_current_user_info] = lambda: professor_user

    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")

    assert response.status_code == 200
    waiting_rooms = response.json()

    # Should be a list with 3 waiting rooms
    assert isinstance(waiting_rooms, list)
    assert len(waiting_rooms) == 3


@pytest.mark.asyncio
async def test_get_professor_waiting_rooms_all_states(client, professor_user, setup_waiting_rooms, session):
    """Test that all waiting room states are correctly returned."""
    app.dependency_overrides[get_current_user_info] = lambda: professor_user

    response = await client.get("/api/waiting-rooms/professor/my-waiting-rooms")

    assert response.status_code == 200
    waiting_rooms = response.json()

    # Collect all states and roles
    states_found = set(wr["state"] for wr in waiting_rooms)
    roles_found = set(wr["role"] for wr in waiting_rooms)

    # Should have all three states
    assert "preparation" in states_found
    assert "running" in states_found
    assert "closed" in states_found

    # Should have both roles
    assert "regent" in roles_found
    assert "vigilant" in roles_found
