import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import ValidationError
from src.services.question import create_question_XML, get_question_options_by_question_id, update_question
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.question import Question, QuestionUpdate
from src.models.question_option import QuestionOption

@pytest.mark.asyncio
async def test_create_question_XML_topic_exists(session):
    sub = Subject(name="XML Sub")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    t = Topic(name="T1", subject_id=sub.id)
    session.add(t)
    await session.commit()
    
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <quiz>
      <question type="multichoice">
        <name><text>T1</text></name>
        <questiontext><text>Q1</text></questiontext>
        <answer fraction="100"><text>A1</text></answer>
      </quiz>
    </quiz>
    """
    result = await create_question_XML(session, sub.id, xml)
    assert result["topics_created"] == 0
    assert result["questions_created"] == 1

@pytest.mark.asyncio
async def test_update_question_not_found(session):
    with pytest.raises(Exception, match="Question not found"):
        await update_question(session, QuestionUpdate(id=9999, question_text="New"))

@pytest.mark.asyncio
async def test_get_question_options_validation_error(session):
    sub = Subject(name="Val Sub")
    session.add(sub)
    await session.commit()
    t = Topic(name="T", subject_id=sub.id)
    session.add(t)
    await session.commit()
    q = Question(topic_id=t.id, question_text="Q")
    session.add(q)
    await session.commit()
    await session.refresh(q)
    
    # Add an invalid option manually (e.g. missing text if not nullable, but let's just mock)
    # Actually, QuestionOptionPublic.model_validate(item) is where it happens.
    # Let's mock the model_validate to raise ValidationError
    with patch("src.models.question_option.QuestionOptionPublic.model_validate", side_effect=ValidationError.from_exception_data(title="err", line_errors=[])):
        opt = QuestionOption(question_id=q.id, option_text="O", value=True)
        session.add(opt)
        await session.commit()
        
        opts = await get_question_options_by_question_id(session, q.id)
        assert opts == []
