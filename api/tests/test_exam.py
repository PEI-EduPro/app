import pytest
from src.core.deps import get_current_user_info
from src.main import app
from unittest.mock import patch, AsyncMock, MagicMock

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
    
    topic = Topic(name="Exam Topic", subject_id=sub.id)
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
            "topics": ["Exam Topic"],
            "number_questions": {"Exam Topic": 2},
            "relative_quotations": {"Exam Topic": 1.0},
            "num_variations": 1
        }

        response = await client.post("/api/exams/generate", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        # Content should be a zip file (which we mocked to be created from dummy pdfs)
        assert len(response.content) > 0
