import pytest
from src.core.deps import get_current_user_info
from src.main import app
from src.models.subject import Subject
from src.models.topic import Topic

@pytest.fixture
async def setup_topic(session):
    sub = Subject(name="Question Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    topic = Topic(name="Question Topic", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return topic

@pytest.mark.asyncio
async def test_create_questions(client, mock_auth, setup_topic):
    app.dependency_overrides[get_current_user_info] = mock_auth
    topic = setup_topic
    
    payload = [
        {
            "topic_id": topic.id,
            "question_text": "What is 2+2?",
            "question_options": [
                {"option_text": "4", "value": True},
                {"option_text": "5", "value": False}
            ]
        }
    ]
    
    response = await client.post("/api/questions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["question_text"] == "What is 2+2?"

@pytest.mark.asyncio
async def test_get_question_and_options(client, session, setup_topic):
    topic = setup_topic
    from src.models.question import Question, QuestionCreate
    from src.services.question import create_question
    
    q_data = [
        QuestionCreate(
            topic_id=topic.id,
            question_text="Test Question",
            question_options=[
                 {"option_text": "Yes", "value": True},
                 {"option_text": "No", "value": False}
            ]
        )
    ]
    # Use service directly or endpoint? Endpoint is better for integration-ish unit test
    # But let's assume we want to test GET
    questions = await create_question(session, q_data)
    q_id = questions[0].id
    
    # Get Question
    response = await client.get(f"/api/questions/{q_id}")
    assert response.status_code == 200
    assert response.json()["question_text"] == "Test Question"
    
    # Get Options
    response_opts = await client.get(f"/api/questions/{q_id}/question-options")
    assert response_opts.status_code == 200
    opts = response_opts.json()
    assert len(opts) == 2
    texts = [o["option_text"] for o in opts]
    assert "Yes" in texts
    assert "No" in texts
