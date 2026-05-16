import pytest
from unittest.mock import patch, AsyncMock
from src.core.deps import get_current_user_info
from src.main import app
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.question import Question, QuestionCreate
from src.services.question import create_question
from src.models.question_option import QuestionOption

@pytest.fixture
async def setup_question(session):
    sub = Subject(name="Option Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    topic = Topic(name="Option Topic", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    q_data = [
        QuestionCreate(
            topic_id=topic.id,
            question_text="Option Test Question",
            question_options=[]
        )
    ]
    questions = await create_question(session, q_data)
    return questions[0]

@pytest.mark.asyncio
async def test_create_question_options(client, mock_auth, setup_question):
    app.dependency_overrides[get_current_user_info] = mock_auth
    question = setup_question
    
    payload = [
        {
            "question_id": question.id,
            "option_text": "Option 1",
            "value": True
        },
        {
            "question_id": question.id,
            "option_text": "Option 2",
            "value": False
        }
    ]
    
    response = await client.post("/api/question-options/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    texts = [o["option_text"] for o in data]
    assert "Option 1" in texts
    assert "Option 2" in texts

@pytest.mark.asyncio
async def test_create_duplicate_question_options(client, mock_auth, setup_question):
    app.dependency_overrides[get_current_user_info] = mock_auth
    question = setup_question
    
    payload = [
        {
            "question_id": question.id,
            "option_text": "Duplicate Option",
            "value": True
        },
        {
            "question_id": question.id,
            "option_text": "Duplicate Option",
            "value": False
        }
    ]
    
    response = await client.post("/api/question-options/", json=payload)
    assert response.status_code == 400
    assert "Duplicate option texts" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_question_option(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    question = setup_question
    
    # Create an option directly in the DB
    option = QuestionOption(question_id=question.id, option_text="Old Text", value=False)
    session.add(option)
    await session.commit()
    await session.refresh(option)
    
    payload = {
        "option_text": "New Text",
        "value": True
    }
    
    response = await client.put(f"/api/question-options/{option.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["option_text"] == "New Text"
    assert data["value"] is True

@pytest.mark.asyncio
async def test_update_question_option_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    payload = {
        "option_text": "Ghost Option",
        "value": True
    }
    
    response = await client.put("/api/question-options/99999", json=payload)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_question_option(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    question = setup_question
    
    # Create an option directly in the DB
    option = QuestionOption(question_id=question.id, option_text="To Delete", value=False)
    session.add(option)
    await session.commit()
    await session.refresh(option)
    
    response = await client.delete(f"/api/question-options/{option.id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Question option deleted successfully"
    
    # Verify it's gone
    deleted = await session.get(QuestionOption, option.id)
    assert deleted is None

@pytest.mark.asyncio
async def test_delete_question_option_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    
    response = await client.delete("/api/question-options/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_question_options_empty(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    response = await client.post("/api/question-options/", json=[])
    assert response.status_code == 400
    assert "No question options provided" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_question_options_question_not_found(client, mock_auth):
    app.dependency_overrides[get_current_user_info] = mock_auth
    payload = [{"question_id": 99999, "option_text": "O", "value": True}]
    response = await client.post("/api/question-options/", json=payload)
    assert response.status_code == 400
    assert "Question 99999 not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_question_options_topic_not_found(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    # Mock topic_service to return None
    with patch("src.routers.question_option.topic_service.get_topic_by_id", return_value=None):
        payload = [{"question_id": setup_question.id, "option_text": "O", "value": True}]
        response = await client.post("/api/question-options/", json=payload)
        assert response.status_code == 400
        assert f"Topic {setup_question.topic_id} not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_question_options_internal_error(client, mock_auth, setup_question):
    app.dependency_overrides[get_current_user_info] = mock_auth
    with patch("src.routers.question_option.question_option.create_question_options", side_effect=Exception("Boom")):
        payload = [{"question_id": setup_question.id, "option_text": "O", "value": True}]
        response = await client.post("/api/question-options/", json=payload)
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_update_question_option_service_fails(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    option = QuestionOption(question_id=setup_question.id, option_text="Old", value=False)
    session.add(option)
    await session.commit()
    
    with patch("src.routers.question_option.question_option.update_question_option", return_value=None):
        response = await client.put(f"/api/question-options/{option.id}", json={"option_text": "New"})
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_question_option_internal_error(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    option = QuestionOption(question_id=setup_question.id, option_text="Old", value=False)
    session.add(option)
    await session.commit()
    
    with patch("src.routers.question_option.question_option.update_question_option", side_effect=Exception("Boom")):
        response = await client.put(f"/api/question-options/{option.id}", json={"option_text": "New"})
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_delete_question_option_service_fails(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    option = QuestionOption(question_id=setup_question.id, option_text="Old", value=False)
    session.add(option)
    await session.commit()
    
    with patch("src.routers.question_option.question_option.delete_question_option", return_value=False):
        response = await client.delete(f"/api/question-options/{option.id}")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_question_option_internal_error(client, mock_auth, setup_question, session):
    app.dependency_overrides[get_current_user_info] = mock_auth
    option = QuestionOption(question_id=setup_question.id, option_text="Old", value=False)
    session.add(option)
    await session.commit()
    
    with patch("src.routers.question_option.question_option.delete_question_option", side_effect=Exception("Boom")):
        response = await client.delete(f"/api/question-options/{option.id}")
        assert response.status_code == 500

