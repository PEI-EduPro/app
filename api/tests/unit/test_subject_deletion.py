import pytest
from src.core.deps import get_current_user_info
from src.main import app
from unittest.mock import patch, AsyncMock, MagicMock
from sqlmodel import select

@pytest.mark.asyncio
async def test_delete_subject_comprehensive(client, mock_auth, session):
    """Test comprehensive deletion of subject and its exam configs."""
    # We need a manager user to delete a subject (as per require_manager dependency)
    from src.models.user import User
    manager_user = User(
        user_id="manager-id",
        username="manager",
        email="manager@test.com",
        realm_roles=["manager"],
        groups=[]
    )
    
    async def override_get_current_user_info():
        return manager_user
    
    app.dependency_overrides[get_current_user_info] = override_get_current_user_info

    from src.models.subject import Subject
    from src.models.exam_config import ExamConfig
    from src.models.topic import Topic

    # 1. Setup Test Data
    subject = Subject(name="Subject to Delete")
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    
    topic = Topic(name="Topic to Delete", subject_id=subject.id)
    session.add(topic)
    
    exam_config = ExamConfig(subject_id=subject.id, fraction=50)
    session.add(exam_config)
    await session.commit()
    await session.refresh(exam_config)

    # 2. Mock exam_service.delete_exam_config and keycloak_client
    with patch("src.services.subject.delete_exam_config", new_callable=AsyncMock) as mock_exam_delete, \
         patch("src.services.subject.keycloak_client.delete_subject_groups", new_callable=AsyncMock) as mock_kc_subject_delete:
        
        async def side_effect_delete(s, ec_id):
            ec = await s.get(ExamConfig, ec_id)
            if ec:
                await s.delete(ec)
            return True
            
        mock_exam_delete.side_effect = side_effect_delete
        mock_kc_subject_delete.return_value = True

        # 3. Execute Deletion
        response = await client.delete(f"/api/subjects/{subject.id}")
        
        assert response.status_code == 204
        
        # 4. Verify Exam Deletion was called
        mock_exam_delete.assert_called_once_with(session, exam_config.id)
        
        # 5. Verify Subject Keycloak Deletion was called
        mock_kc_subject_delete.assert_called_once_with(str(subject.id))
        
        # 6. Verify Subject DB Deletion
        assert (await session.get(Subject, subject.id)) is None
        assert (await session.get(Topic, topic.id)) is None
        # Note: exam_config itself is deleted by the MOCKED delete_exam_config in this test, 
        # but since we mocked it, the DB record might still exist unless the mock does something.
        # However, the focus here is verifying the CALL to the improved deletion method.
