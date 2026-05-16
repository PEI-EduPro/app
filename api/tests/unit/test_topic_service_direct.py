import pytest
from src.services.topic import create_topic, get_all_topics, get_topic_by_id, update_topic, delete_topic
from src.models.topic import TopicCreate, TopicUpdate
from src.models.subject import Subject
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_topic_service_full_coverage(session):
    # 1. Setup Subject
    subject = Subject(name="Math")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    # 2. Test create_topic
    topic_data = TopicCreate(name="Algebra", subject_id=subject.id)
    created_topic = await create_topic(session, topic_data)
    assert created_topic.name == "Algebra"
    assert created_topic.id is not None
    
    # 3. Test get_all_topics (Hits lines 23-25)
    all_topics = await get_all_topics(session)
    assert len(all_topics) >= 1
    assert any(t.name == "Algebra" for t in all_topics)
    
    # 4. Test get_topic_by_id
    topic = await get_topic_by_id(session, created_topic.id)
    assert topic.name == "Algebra"
    
    # 5. Test get_topic_by_id (not found)
    not_found_topic = await get_topic_by_id(session, 99999)
    assert not_found_topic is None
    
    # 6. Test update_topic (Hits lines 43-56)
    update_data = TopicUpdate(name="Linear Algebra")
    updated_topic = await update_topic(session, update_data, created_topic.id)
    assert updated_topic.name == "Linear Algebra"
    
    # 7. Test update_topic (not found)
    with pytest.raises(HTTPException) as excinfo:
        await update_topic(session, update_data, 99999)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Topic not found"
    
    # 8. Test delete_topic (Hits lines 61-70)
    delete_result = await delete_topic(session, created_topic.id)
    assert delete_result is True
    
    # 9. Test delete_topic (not found)
    delete_result_nf = await delete_topic(session, 99999)
    assert delete_result_nf is False
