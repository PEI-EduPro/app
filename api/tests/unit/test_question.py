import pytest
from unittest.mock import patch, AsyncMock
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
async def test_get_question_and_options(client, mock_auth, session, setup_topic):
    app.dependency_overrides[get_current_user_info] = mock_auth
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

@pytest.mark.asyncio
async def test_create_question_invalid_topic(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    payload = [
        {
            "topic_id": 99999,
            "question_text": "Impossible Question",
            "question_options": []
        }
    ]
    
    response = await client.post("/api/questions/", json=payload)
    # Should fail due to FK constraint
    assert response.status_code in [400, 403, 500]

@pytest.mark.asyncio
async def test_get_question_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.get("/api/questions/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_question_empty_list(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/questions/", json=[])
    assert response.status_code == 400
    assert "No questions provided" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_question_from_xml(client, mock_auth, setup_topic):
    app.dependency_overrides[get_current_user_info] = mock_auth
    topic = setup_topic
    from unittest.mock import patch
    with patch("src.routers.question.question.create_question_XML", new_callable=AsyncMock) as mock_xml:
        mock_xml.return_value = {
            "topics_created": 1,
            "questions_created": 1,
            "options_created": 1
        }
        response = await client.post(f"/api/questions/{topic.subject_id}/XML", content="<xml/>", headers={"Content-Type": "application/xml"})
        assert response.status_code == 200
        assert response.json()["topics_created"] == 1

@pytest.mark.asyncio
async def test_put_question_success(client, mock_auth, session, setup_topic):
    app.dependency_overrides[get_current_user_info] = mock_auth
    topic = setup_topic
    from src.models.question import Question
    q = Question(topic_id=topic.id, question_text="Old")
    session.add(q)
    await session.commit()
    await session.refresh(q)
    
    response = await client.put(f"/api/questions/{q.id}", json={"id": q.id, "question_text": "New"})
    assert response.status_code == 200
    assert response.json()["question_text"] == "New"

@pytest.mark.asyncio
async def test_delete_question_success(client, mock_auth, session, setup_topic):
    app.dependency_overrides[get_current_user_info] = mock_auth
    topic = setup_topic
    from src.models.question import Question
    q = Question(topic_id=topic.id, question_text="To Delete")
    session.add(q)
    await session.commit()
    await session.refresh(q)
    
    response = await client.delete(f"/api/questions/{q.id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()

@pytest.mark.asyncio
async def test_put_question_value_error(client, mock_auth, session, setup_topic):
    app.dependency_overrides[get_current_user_info] = mock_auth
    topic = setup_topic
    from src.models.question import Question
    q = Question(topic_id=topic.id, question_text="Old")
    session.add(q)
    await session.commit()
    
    with patch("src.routers.question.question.update_question", side_effect=ValueError("Bad update")):
        response = await client.put(f"/api/questions/{q.id}", json={"id": q.id, "topic_id": topic.id, "question_text": "New"})
        assert response.status_code == 400
        assert "Bad update" in response.json()["detail"]
