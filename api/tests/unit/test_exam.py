import pytest
import json
import io
from src.core.deps import get_current_user_info
from src.main import app
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generate_exam(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth

    # Mock DB setup
    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.question import Question, QuestionCreate
    from src.services.question import create_question

    # 1. Setup Data
    sub = Subject(name="Exam Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    topic = Topic(name="Test Topic", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    # Add enough questions
    q_data = []
    for i in range(5):
        q_data.append(QuestionCreate(
            topic_id=topic.id,
            question_text=f"Q{i}",
            question_options=[{"option_text": "A", "value": True}]
        ))
    await create_question(session, q_data)

    # 2. Mock PDF Generation internals
    # We don't want to actually run latex or zip in unit tests generally, 
    # but the service code is tightly coupled.
    # We will mock `src.services.exam.shutil.which` to pretend pdflatex exists
    # And `src.services.exam.subprocess.run` to skip compilation
    # And `src.services.exam._compile_latex` to return dummy bytes
    
    with patch("src.services.exam.shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("src.services.exam._compile_latex", return_value=b"%PDF-1.4 dummy"), \
         patch("src.services.exam._write_blank_answers"), \
         patch("src.services.exam._write_all_solutions"), \
         patch("src.services.exam._update_rules"):

        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "exam_title": "Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 2},
            "relative_quotations": {str(topic.id): 1.0},
            "num_variations": 1
        }

        response = await client.post("/api/exams/generate", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        # Content should be a zip file (which we mocked to be created from dummy pdfs)
        assert len(response.content) > 0


@pytest.mark.asyncio
async def test_get_subject_exam_configs(client, mock_auth, session):
    """Test retrieving exam configurations for a subject"""
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.exam_config import ExamConfig
    from src.models.topic_config import TopicConfig
    
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    topic_config = TopicConfig(
        exam_config_id=exam_config.id,
        topic_id=topic.id,
        num_questions=5,
        relative_weight=1.0
    )
    session.add(topic_config)
    await session.commit()
    
    response = await client.get(f"/api/exams/subject/{subject.id}/configs")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["subject_id"] == subject.id
    assert data[0]["fraction"] == 50
    assert len(data[0]["topic_configs"]) == 1
    assert data[0]["topic_configs"][0]["topic_name"] == "Test Topic"


@pytest.mark.asyncio
async def test_store_student_list(client, mock_auth, session):
    """Test storing student list via CSV upload"""
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Create CSV content
    csv_content = "nmec,name,email\n12345,John Doe,john@doe.com\n67890,Jane Smith,jane@smith.com"
    csv_file = io.BytesIO(csv_content.encode())
    
    files = {"file": ("students.csv", csv_file, "text/csv")}
    
    response = await client.post(
        f"/api/exams/exam/{exam_config.id}/student_list",
        files=files
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Student list stored successfully."
    
    # Verify data was stored
    await session.refresh(exam_config)
    stored_data = json.loads(exam_config.nmec_name_list)
    assert stored_data["12345"]["name"] == "John Doe"
    assert stored_data["12345"]["email"] == "john@doe.com"
    assert stored_data["67890"]["name"] == "Jane Smith"
    assert stored_data["67890"]["email"] == "jane@smith.com"


@pytest.mark.asyncio
async def test_retrieve_student_list(client, mock_auth, session):
    """Test retrieving stored student list"""
    # Create a user with waiting room permissions
    from src.models.user import User
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from unittest.mock import patch
    
    vigilant_user = User(
        user_id="vigilant-id-123",
        username="vigilant",
        email="vigilant@example.com",
        realm_roles=["vigilant"],
        groups=["/w1/vigilante"]
    )
    
    async def override_get_current_user_info():
        return vigilant_user
    
    app.dependency_overrides[get_current_user_info] = override_get_current_user_info
    
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    student_data = json.dumps({"12345": "John Doe", "67890": "Jane Smith"})
    exam_config = ExamConfig(
        subject_id=subject.id, 
        fraction=50,
        nmec_name_list=student_data
    )
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Mock the ExamConfigResponse.model_validate to avoid relationship loading issues
    with patch("src.routers.exam.ExamConfigResponse.model_validate") as mock_validate:
        mock_validate.return_value = {
            "id": exam_config.id,
            "subject_id": subject.id,
            "fraction": 50,
            "topic_configs": [],
            "nmec_name_list": student_data
        }
        
        response = await client.get(f"/api/exams/exam/{exam_config.id}/student_list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["subject_id"] == subject.id
        assert data["nmec_name_list"] == student_data


@pytest.mark.asyncio
async def test_store_student_list_invalid_file_type(client, mock_auth, session):
    """Test storing student list with invalid file type"""
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    
    # Setup test data
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    # Create invalid file
    txt_content = "not a csv file"
    txt_file = io.BytesIO(txt_content.encode())
    
    files = {"file": ("students.txt", txt_file, "text/plain")}
    
    response = await client.post(
        f"/api/exams/exam/{exam_config.id}/student_list",
        files=files
    )
    
    # Should still work as text/plain is accepted
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_retrieve_student_list_nonexistent_config(client, mock_auth, session):
    """Test retrieving student list for non-existent exam config"""
    # Create a user with waiting room permissions
    from src.models.user import User
    vigilant_user = User(
        user_id="vigilant-id-123",
        username="vigilant",
        email="vigilant@example.com",
        realm_roles=["vigilant"],
        groups=["/w99999/vigilante"]  # Permission for non-existent config
    )
    
    async def override_get_current_user_info():
        return vigilant_user
    
    app.dependency_overrides[get_current_user_info] = override_get_current_user_info
    
    response = await client.get("/api/exams/exam/99999/student_list")
    
    assert response.status_code == 404
    data = response.json()
    assert "Exam configuration not found" in data["detail"]


@pytest.mark.asyncio
async def test_generate_exam_with_student_tuples(client, mock_auth, session):
    """Test generate exam endpoint with student tuples"""
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.question import QuestionCreate
    from src.services.question import create_question

    # Setup test data
    sub = Subject(name="Exam Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    topic = Topic(name="Exam Topic", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    # Add questions
    q_data = []
    for i in range(5):
        q_data.append(QuestionCreate(
            topic_id=topic.id,
            question_text=f"Q{i}",
            question_options=[{"option_text": "A", "value": True}]
        ))
    await create_question(session, q_data)

    with patch("src.services.exam.shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("src.services.exam._compile_latex", return_value=b"%PDF-1.4 dummy"), \
         patch("src.services.exam._write_blank_answers"), \
         patch("src.services.exam._write_all_solutions"), \
         patch("src.services.exam._update_rules"), \
         patch("src.services.waiting_room.keycloak_client.create_waiting_room_groups", new_callable=AsyncMock) as mock_wr_kc:

        mock_wr_kc.return_value = True

        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "exam_title": "Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 2},
            "relative_quotations": {str(topic.id): 1.0},
            "num_variations": 1,
            "professors": ["Prof A", "Prof B"],
            "student_tuples": [
                [12345, "John Doe", "john@example.com"],
                [67890, "Jane Smith", "jane@example.com"]
            ]
        }

        response = await client.post("/api/exams/generate", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        
        # Verify student data was stored in exam config
        from src.services.exam import get_latest_exam_config_id, get_exam_config_by_id
        config_id = await get_latest_exam_config_id(session, sub.id)
        exam_config = await get_exam_config_by_id(session, config_id)
        
        assert exam_config.nmec_name_list is not None
        student_data = json.loads(exam_config.nmec_name_list)
        assert "12345" in student_data
        assert student_data["12345"]["name"] == "John Doe"
        assert student_data["12345"]["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_get_submitted_exams_count(client, mock_auth, session):
    """Test counting exams submitted for OMR correction (have a capture_path)"""
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.exam import Exam
    from src.models.waiting_room import WaitingRoom

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    waiting_room = WaitingRoom(exam_config_id=exam_config.id)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)

    # 2 submitted (have capture_path), 1 not submitted
    session.add(Exam(exam_config_id=exam_config.id, capture_path="/some/path/1.jpg"))
    session.add(Exam(exam_config_id=exam_config.id, capture_path="/some/path/2.jpg"))
    session.add(Exam(exam_config_id=exam_config.id, capture_path=None))
    await session.commit()

    response = await client.get(f"/api/waiting-rooms/{waiting_room.id}/submitted_count")

    assert response.status_code == 200
    assert response.json()["submitted_count"] == 2


@pytest.mark.asyncio
async def test_generate_exam_with_waiting_room(client, mock_auth, session):
    """Test generate exam endpoint with waiting room creation"""
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.question import QuestionCreate
    from src.services.question import create_question

    # Setup test data
    sub = Subject(name="Exam Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    topic = Topic(name="Exam Topic", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    # Add questions
    q_data = []
    for i in range(5):
        q_data.append(QuestionCreate(
            topic_id=topic.id,
            question_text=f"Q{i}",
            question_options=[{"option_text": "A", "value": True}]
        ))
    await create_question(session, q_data)

    with patch("src.services.exam.shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("src.services.exam._compile_latex", return_value=b"%PDF-1.4 dummy"), \
         patch("src.services.exam._write_blank_answers"), \
         patch("src.services.exam._write_all_solutions"), \
         patch("src.services.exam._update_rules"), \
         patch("src.services.waiting_room.keycloak_client.create_waiting_room_groups", new_callable=AsyncMock):

        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "exam_title": "Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 2},
            "relative_quotations": {str(topic.id): 1.0},
            "num_variations": 1,
            "vigilant_keycloak_ids": ["vigilant1", "vigilant2"]
        }

        response = await client.post("/api/exams/generate", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        
        # Verify waiting room was created
        from src.services.exam import get_latest_exam_config_id
        from src.services.waiting_room import get_waiting_room
        from sqlmodel import select
        from src.models.waiting_room import WaitingRoom
        
        config_id = await get_latest_exam_config_id(session, sub.id)
        stmt = select(WaitingRoom).where(WaitingRoom.exam_config_id == config_id)
        result = await session.exec(stmt)
        waiting_room = result.first()
        
        assert waiting_room is not None
        assert waiting_room.exam_config_id == config_id
