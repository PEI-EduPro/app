import pytest
import os
import json
from src.core.deps import get_current_user_info
from src.main import app
from unittest.mock import patch, AsyncMock, MagicMock
from sqlmodel import select

@pytest.mark.asyncio
async def test_delete_exam_config_comprehensive(client, mock_auth, session):
    """Test comprehensive deletion of exam config and all related data."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.exam import Exam
    from src.models.warning import Warning, WarningType
    from src.models.topic_config import TopicConfig
    from src.models.topic import Topic

    # 1. Setup Test Data
    subject = Subject(name="Deletion Subject")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Deletion Topic", subject_id=subject.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    # Create dummy files
    zip_path = "storage/exams/test_delete.zip"
    capture_path = "storage/captures/test_capture.jpg"
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    os.makedirs(os.path.dirname(capture_path), exist_ok=True)
    with open(zip_path, "w") as f: f.write("dummy zip")
    with open(capture_path, "w") as f: f.write("dummy image")

    exam_config = ExamConfig(subject_id=subject.id, fraction=50, zip_path=zip_path)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)
    
    topic_config = TopicConfig(exam_config_id=exam_config.id, topic_id=topic.id, num_questions=5, relative_weight=1.0)
    session.add(topic_config)
    
    exam_item = Exam(exam_config_id=exam_config.id, capture_path=capture_path)
    session.add(exam_item)
    
    warning = Warning(exam_config_id=exam_config.id, type=WarningType.multiple_students_to_exam)
    session.add(warning)
    await session.commit()

    # 2. Mock Keycloak Deletion
    with patch("src.services.exam.keycloak_client.delete_exam_session_groups", new_callable=AsyncMock) as mock_kc_delete:
        mock_kc_delete.return_value = True

        # 3. Execute Deletion
        response = await client.delete(f"/api/exams/config/{exam_config.id}")
        
        assert response.status_code == 204
        
        # 4. Verify Database Deletion
        assert (await session.get(ExamConfig, exam_config.id)) is None
        assert (await session.get(TopicConfig, topic_config.id)) is None
        assert (await session.get(Exam, exam_item.id)) is None
        assert (await session.get(Warning, warning.id)) is None
        
        # 5. Verify File Deletion
        assert not os.path.exists(zip_path)
        assert not os.path.exists(capture_path)
        
        # 6. Verify Keycloak Call
        mock_kc_delete.assert_called_once_with(exam_config.id)

    # Cleanup if needed (though os.path.exists check should be enough)
    if os.path.exists(zip_path): os.remove(zip_path)
    if os.path.exists(capture_path): os.remove(capture_path)


@pytest.mark.asyncio
async def test_delete_exam_config_not_found(session):
    """Test deleting non-existent exam configuration returns False"""
    from src.services.exam import delete_exam_config
    result = await delete_exam_config(session, 9999)
    assert result is False


@pytest.mark.asyncio
async def test_delete_exam_config_file_remove_fail(session):
    """Test delete_exam_config handles file removal failures gracefully"""
    from src.services.exam import delete_exam_config
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig

    subject = Subject(name="Test")
    session.add(subject)
    await session.commit()
    
    ec = ExamConfig(subject_id=subject.id, zip_path="/fake/path.zip")
    session.add(ec)
    await session.commit()
    
    with patch("os.path.exists", return_value=True), \
         patch("os.remove", side_effect=Exception("Perm error")), \
         patch("src.services.exam.keycloak_client.delete_exam_session_groups", new_callable=AsyncMock) as mock_kc:
        mock_kc.return_value = True
        result = await delete_exam_config(session, ec.id)
        assert result is True


@pytest.mark.asyncio
async def test_delete_exam_config_keycloak_fail(session):
    """Test delete_exam_config handles Keycloak group deletion failures gracefully"""
    from src.services.exam import delete_exam_config
    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig

    subject = Subject(name="Test")
    session.add(subject)
    await session.commit()
    
    ec = ExamConfig(subject_id=subject.id)
    session.add(ec)
    await session.commit()
    
    with patch("src.services.exam.keycloak_client.delete_exam_session_groups", side_effect=Exception("KC error")):
        result = await delete_exam_config(session, ec.id)
        assert result is True
