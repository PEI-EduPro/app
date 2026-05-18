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
            "total_exams": 1
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
    from src.models.exam_config import ExamConfig, ExamState
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
    from src.models.exam_config import ExamConfig, ExamState
    
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
    from src.models.exam_config import ExamConfig, ExamState
    from unittest.mock import patch
    
    vigilant_user = User(
        user_id="vigilant-id-123",
        username="vigilant",
        email="vigilant@example.com",
        realm_roles=["vigilant"],
        groups=["/w1/vigilant"]
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
            "nmec_name_list": student_data,
            "total_exams": 0,
            "status": "PENDING",
            "state": "preparing",
            "associations": []
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
    from src.models.exam_config import ExamConfig, ExamState
    
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
        groups=["/w99999/vigilant"]  # Permission for non-existent config
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
         patch("src.routers.exam.create_exam_session_groups_service", new_callable=AsyncMock) as mock_wr_kc:

        mock_wr_kc.return_value = True

        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "exam_title": "Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 2},
            "relative_quotations": {str(topic.id): 1.0},
            "total_exams": 1,
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
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.exam import Exam

    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    # 2 submitted (have capture_path), 1 not submitted
    session.add(Exam(exam_config_id=exam_config.id, capture_path="/some/path/1.jpg"))
    session.add(Exam(exam_config_id=exam_config.id, capture_path="/some/path/2.jpg"))
    session.add(Exam(exam_config_id=exam_config.id, capture_path=None))
    await session.commit()

    response = await client.get(f"/api/exams/{exam_config.id}/session/submitted_count")

    assert response.status_code == 200
    assert response.json()["submitted_count"] == 2


@pytest.mark.asyncio
async def test_generate_exam_with_session(client, mock_auth, session):
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
         patch("src.routers.exam.create_exam_session_groups_service", new_callable=AsyncMock):

        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "exam_title": "Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 2},
            "relative_quotations": {str(topic.id): 1.0},
            "total_exams": 1,
            "vigilant_keycloak_ids": ["vigilant1", "vigilant2"]
        }

        response = await client.post("/api/exams/generate", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        
        # Verify exam config was created
        from src.services.exam import get_latest_exam_config_id
        from src.models.exam_config import ExamConfig, ExamState
        from sqlmodel import select
        
        config_id = await get_latest_exam_config_id(session, sub.id)
        config = await session.get(ExamConfig, config_id)
        
        assert config is not None
        assert config.subject_id == sub.id

@pytest.mark.asyncio
async def test_generate_exams_no_subject_id(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/generate", json={})
    assert response.status_code == 400
    assert "subject_id is required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_exams_value_error(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    
    with patch("src.routers.exam.create_configs_and_exams", side_effect=ValueError("Invalid spec")):
        response = await client.post("/api/exams/generate", json={"subject_id": sub.id})
        assert response.status_code == 400
        assert "Invalid spec" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_exams_async_success(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.topic_config import TopicConfig
    
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    topic = Topic(name="T", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    exam_config = ExamConfig(id=1, subject_id=sub.id, fraction=0)
    topic_config = TopicConfig(id=1, exam_config_id=1, topic_id=topic.id, num_questions=1, relative_weight=1.0)
    
    with patch("src.routers.exam.create_configs", return_value=(exam_config, [topic_config])), \
         patch("src.routers.exam.create_exam_session_groups_service", new_callable=AsyncMock), \
         patch("src.routers.exam.generate_exams_task"):
        
        payload = {"subject_id": sub.id, "total_exams": 1}
        response = await client.post("/api/exams/generate_async", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_get_config_status(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState, GenerationStatus
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, status=GenerationStatus.COMPLETED)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)
    
    response = await client.get(f"/api/exams/config/{ec.id}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_download_exam_zip_not_ready(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState, GenerationStatus
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, status=GenerationStatus.PENDING)
    session.add(ec)
    await session.commit()
    await session.refresh(ec)
    
    response = await client.get(f"/api/exams/config/{ec.id}/download")
    assert response.status_code == 400
    assert "Generation is not completed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_validate_exam_success(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.exam import Exam
    
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, grade=10, results="{}", capture_path="p")
    session.add(e)
    await session.commit()
    await session.refresh(e)
    
    response = await client.post(f"/api/exams/{e.id}/validate")
    assert response.status_code == 200
    await session.refresh(e)
    assert e.validated is True

@pytest.mark.asyncio
async def test_correct_by_hand_job(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.exam import Exam
    
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id)
    session.add(e)
    await session.commit()
    await session.refresh(e)
    
    with patch("src.routers.exam.correct_by_hand", new_callable=AsyncMock) as mock_cbh:
        mock_cbh.return_value = e
        response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json={"grid": {}})
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_subject_exam_configs_missing_topic(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState, ExamState, GenerationStatus
    from src.models.topic_config import TopicConfig
    
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    
    # Mock return value to simulate missing topic in relationship
    mock_tc = MagicMock()
    mock_tc.id = 1
    mock_tc.topic_id = 999
    mock_tc.topic = None
    mock_tc.num_questions = 1
    mock_tc.relative_weight = 1.0
    
    mock_config = MagicMock()
    mock_config.id = 1
    mock_config.subject_id = sub.id
    mock_config.fraction = 0
    mock_config.topic_configs = [mock_tc]
    mock_config.nmec_name_list = None
    mock_config.exam_name = "Test Exam"
    mock_config.exam_date = "2026-05-18"
    mock_config.num_versions = 1
    mock_config.exams = []
    mock_config.status = GenerationStatus.COMPLETED
    mock_config.state = ExamState.PREPARING
    mock_config.associations = []

    with patch("src.routers.exam.get_exam_configs_by_subject", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [mock_config]
        response = await client.get(f"/api/exams/subject/{sub.id}/configs")
        assert response.status_code == 200
        assert response.json()[0]["topic_configs"][0]["topic_name"] == "Unknown Topic"

@pytest.mark.asyncio
async def test_generate_exams_validation_error(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    
    with patch("src.routers.exam.create_configs_and_exams", side_effect=ValueError("Invalid config")):
        response = await client.post("/api/exams/generate", json={"subject_id": sub.id})
        assert response.status_code == 400
        assert "Invalid config" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_exams_internal_error(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    
    with patch("src.routers.exam.create_configs_and_exams", side_effect=Exception("Internal Boom")):
        response = await client.post("/api/exams/generate", json={"subject_id": sub.id})
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_generate_exams_async_no_subject_id(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/generate_async", json={})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_generate_exams_async_internal_error(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    
    with patch("src.routers.exam.create_configs", side_effect=Exception("Async fail")):
        response = await client.post("/api/exams/generate_async", json={"subject_id": sub.id})
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_get_config_status_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/config/99999/status")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_download_exam_zip_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/config/99999/download")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_download_exam_zip_file_missing_on_disk(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState, GenerationStatus
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, status=GenerationStatus.COMPLETED, zip_path="/tmp/nonexistent.zip")
    session.add(ec)
    await session.commit()
    
    response = await client.get(f"/api/exams/config/{ec.id}/download")
    assert response.status_code == 404
    assert "Generated ZIP file not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_store_student_list_config_not_found(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState, ExamState

    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()

    
    with patch("src.routers.exam.get_exam_config_by_id", return_value=None):
        csv_file = io.BytesIO(b"n,m,e\n1,J,j")
        files = {"file": ("s.csv", csv_file, "text/csv")}
        response = await client.post(f"/api/exams/exam/{ec.id}/student_list", files=files)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_retrieve_student_list_value_error(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.exam.get_subject_id_by_exam_config_id", side_effect=ValueError("Not found")):
        response = await client.get("/api/exams/exam/999/student_list")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_exam_config_wrong_state(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState, ExamState
    
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    
    response = await client.delete(f"/api/exams/config/{ec.id}")
    assert response.status_code == 400
    assert "It must be in 'preparing' or 'sent' state" in response.json()["detail"]
@pytest.mark.asyncio
async def test_delete_exam_config_value_error(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.exam.get_subject_id_by_exam_config_id", side_effect=ValueError("Bad ID")):
        response = await client.delete("/api/exams/config/999")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_validate_exam_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/exams/99999/validate")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_validate_exam_not_corrected_yet(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.exam import Exam
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, grade=None) # Not corrected
    session.add(e)
    await session.commit()
    
    response = await client.post(f"/api/exams/{e.id}/validate")
    assert response.status_code == 400
    assert "Exam has not been corrected yet" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_all_exams_info_success(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.exam import Exam
    
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, fraction=0.5)
    session.add(ec)
    await session.commit()
    
    e = Exam(
        exam_config_id=ec.id, 
        grade=15.0, 
        results="{}", 
        capture_path="cap", 
        correction_path="corr"
    )
    session.add(e)
    await session.commit()
    
    # Mock base64 read
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", return_value=io.BytesIO(b"fake_image")), \
         patch("src.routers.exam.base64.b64encode", return_value=b"YmFzZTY0"):
        
        response = await client.get(f"/api/exams/{ec.id}/all_exams_info")
        assert response.status_code == 200
        assert response.json()[0]["capture"] == "YmFzZTY0"

@pytest.mark.asyncio
async def test_get_all_exams_info_config_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/99999/all_exams_info")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_exam_info_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/99999/exam_info")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_correct_by_hand_job_value_error(client, mock_auth, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig, ExamState
    from src.models.exam import Exam
    sub = Subject(name="S")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.VALIDATION)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id)
    session.add(e)
    await session.commit()
    
    with patch("src.routers.exam.correct_by_hand", side_effect=ValueError("Invalid grid")):
        response = await client.post(f"/api/exams/{e.id}/correct_by_hand_job", json={"grid": {}})
        assert response.status_code == 404
        assert "Invalid grid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_professor_exam_sessions_no_role(client, mock_auth):
    """Test list_professor_exam_sessions requires professor role"""
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/exams/professor/my-exam-sessions")
    assert response.status_code == 403
    assert "Requires professor role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_exam_session_info_not_found(client, mock_auth, session):
    """Test get_exam_session_info returns 404 if config not found"""
    app.dependency_overrides[get_current_user_info] = mock_auth
    # We need to mock permissions because verify_permission is called
    with patch("src.routers.exam.verify_permission"):
        response = await client.get("/api/exams/9999/session/info")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_exam_session_metrics_not_found(client, mock_auth):
    """Test get_exam_session_metrics returns 404 if config not found"""
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.exam.verify_permission"):
        response = await client.get("/api/exams/9999/session/metrics")
        assert response.status_code == 404

