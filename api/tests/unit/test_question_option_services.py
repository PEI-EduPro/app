import pytest
from src.services import question_option as option_service
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.question import Question
from src.models.question_option import QuestionOptionCreate, QuestionOptionUpdate, QuestionOption
from fastapi import HTTPException

@pytest.fixture
async def setup_base_question(session):
    subject = Subject(name="Test Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Test Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    question = Question(topic_id=topic.id, question_text="Service Test Question")
    session.add(question)
    await session.commit()
    await session.refresh(question)
    
    return question

@pytest.mark.asyncio
async def test_create_question_options_service(session, setup_base_question):
    question = setup_base_question
    
    options_data = [
        QuestionOptionCreate(question_id=question.id, option_text="Opt 1", value=True),
        QuestionOptionCreate(question_id=question.id, option_text="Opt 2", value=False)
    ]
    
    created_options = await option_service.create_question_options(session, options_data)
    
    assert len(created_options) == 2
    assert created_options[0].option_text == "Opt 1"
    assert created_options[1].option_text == "Opt 2"

@pytest.mark.asyncio
async def test_create_question_options_service_duplicate_text(session, setup_base_question):
    question = setup_base_question
    
    options_data = [
        QuestionOptionCreate(question_id=question.id, option_text="Same Opt", value=True),
        QuestionOptionCreate(question_id=question.id, option_text="same opt ", value=False)
    ]
    
    with pytest.raises(HTTPException) as exc_info:
        await option_service.create_question_options(session, options_data)
    
    assert exc_info.value.status_code == 400
    assert "Duplicate option texts" in exc_info.value.detail

@pytest.mark.asyncio
async def test_update_question_option_service(session, setup_base_question):
    question = setup_base_question
    
    option = QuestionOption(question_id=question.id, option_text="Initial", value=False)
    session.add(option)
    await session.commit()
    await session.refresh(option)
    
    update_data = QuestionOptionUpdate(option_text="Updated Text", value=True)
    
    updated_option = await option_service.update_question_option(session, option.id, update_data)
    
    assert updated_option is not None
    assert updated_option.option_text == "Updated Text"
    assert updated_option.value is True

@pytest.mark.asyncio
async def test_update_question_option_service_not_found(session):
    update_data = QuestionOptionUpdate(option_text="Updated Text", value=True)
    
    with pytest.raises(HTTPException) as exc_info:
        await option_service.update_question_option(session, 99999, update_data)
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()

@pytest.mark.asyncio
async def test_delete_question_option_service(session, setup_base_question):
    question = setup_base_question
    
    option = QuestionOption(question_id=question.id, option_text="Delete Me", value=False)
    session.add(option)
    await session.commit()
    await session.refresh(option)
    
    result = await option_service.delete_question_option(session, option.id)
    assert result is True
    
    # Verify it's gone
    deleted = await session.get(QuestionOption, option.id)
    assert deleted is None

@pytest.mark.asyncio
async def test_delete_question_option_service_not_found(session):
    result = await option_service.delete_question_option(session, 99999)
    assert result is False
