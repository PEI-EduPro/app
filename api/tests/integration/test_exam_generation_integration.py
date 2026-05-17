import pytest
import json
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_exam_generation_with_students_and_session_integration(client, mock_auth, session):
    """Integration test for exam generation with student tuples and session creation"""
    from src.core.deps import get_current_user_info
    from src.main import app
    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.question import QuestionCreate
    from src.services.question import create_question
    
    app.dependency_overrides[get_current_user_info] = mock_auth

    # Setup test data
    subject = Subject(name="Integration Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Integration Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    # Add questions
    q_data = []
    for i in range(10):
        q_data.append(QuestionCreate(
            topic_id=topic.id,
            question_text=f"Integration Question {i}",
            question_options=[
                {"option_text": "Option A", "value": True},
                {"option_text": "Option B", "value": False}
            ]
        ))
    await create_question(session, q_data)

    # Mock external dependencies
    with patch("src.services.exam.shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("src.services.exam._compile_latex", return_value=b"%PDF-1.4 dummy"), \
         patch("src.services.exam._write_blank_answers"), \
         patch("src.services.exam._write_all_solutions"), \
         patch("src.services.exam._update_rules"), \
         patch("src.routers.exam.create_exam_session_groups_service", new_callable=AsyncMock):

        # Test payload with all new features
        payload = {
            "subject_id": subject.id,
            "fraction": 75,
            "exam_title": "Integration Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 5},
            "relative_quotations": {str(topic.id): 2.0},
            "total_exams": 2,
            "professors": ["Prof. Smith", "Prof. Johnson"],
            "student_tuples": [
                [12345, "Alice Johnson", "alice@university.edu"],
                [67890, "Bob Smith", "bob@university.edu"],
                [11111, "Carol Davis", "carol@university.edu"]
            ],
            "vigilant_keycloak_ids": ["vigilant1", "vigilant2", "vigilant3"]
        }

        # Make the request
        response = await client.post("/api/exams/generate", json=payload)
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert len(response.content) > 0

        # Verify exam config was created with student data
        from src.services.exam import get_latest_exam_config_id, get_exam_config_by_id
        config_id = await get_latest_exam_config_id(session, subject.id)
        exam_config = await get_exam_config_by_id(session, config_id)
        
        # Check exam config properties
        assert exam_config.subject_id == subject.id
        assert exam_config.fraction == 75
        assert exam_config.nmec_name_list is not None
        
        # Verify student data structure
        student_data = json.loads(exam_config.nmec_name_list)
        assert len(student_data) == 3
        assert "12345" in student_data
        assert student_data["12345"]["name"] == "Alice Johnson"
        assert student_data["12345"]["email"] == "alice@university.edu"
        assert "67890" in student_data
        assert student_data["67890"]["name"] == "Bob Smith"
        assert student_data["67890"]["email"] == "bob@university.edu"

        # Verify session was initialized
        from src.models.exam_config import ExamState
        assert exam_config.state == ExamState.PREPARING


@pytest.mark.asyncio
async def test_exam_generation_without_optional_params_integration(client, mock_auth, session):
    """Integration test for exam generation without optional parameters"""
    from src.core.deps import get_current_user_info
    from src.main import app
    from src.models.subject import Subject
    from src.models.topic import Topic
    from src.models.question import QuestionCreate
    from src.services.question import create_question

    app.dependency_overrides[get_current_user_info] = mock_auth

    # Setup test data
    subject = Subject(name="Simple Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)

    topic = Topic(name="Simple Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    # Add questions
    q_data = []
    for i in range(5):
        q_data.append(QuestionCreate(
            topic_id=topic.id,
            question_text=f"Simple Question {i}",
            question_options=[{"option_text": "Answer", "value": True}]
        ))
    await create_question(session, q_data)

    with patch("src.services.exam.shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("src.services.exam._compile_latex", return_value=b"%PDF-1.4 dummy"), \
         patch("src.services.exam._write_blank_answers"), \
         patch("src.services.exam._write_all_solutions"), \
         patch("src.services.exam._update_rules"), \
         patch("src.routers.exam.create_exam_session_groups_service", new_callable=AsyncMock):

        # Minimal payload without new optional parameters
        payload = {
            "subject_id": subject.id,
            "fraction": 50,
            "exam_title": "Simple Test Exam",
            "topics": [str(topic.id)],
            "number_questions": {str(topic.id): 3},
            "relative_quotations": {str(topic.id): 1.0},
            "total_exams": 1
        }

        response = await client.post("/api/exams/generate", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # Verify exam config was created without student data
        from src.services.exam import get_latest_exam_config_id, get_exam_config_by_id
        config_id = await get_latest_exam_config_id(session, subject.id)
        exam_config = await get_exam_config_by_id(session, config_id)

        assert exam_config.subject_id == subject.id
        assert exam_config.fraction == 50
        assert exam_config.nmec_name_list is None

        # Verify session was initialized
        from src.models.exam_config import ExamState
        assert exam_config.state == ExamState.PREPARING
