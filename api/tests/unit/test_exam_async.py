import pytest
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
from fastapi import Response
from src.core.deps import get_current_user_info
from src.main import app
from src.models.exam_config import GenerationStatus, ExamConfig
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.question import QuestionCreate
from src.services.question import create_question
from src.services.exam import generate_exams_task

@pytest.mark.asyncio
async def test_generate_exams_async_endpoint(client, mock_auth, session):
    """Test the POST /generate_async endpoint."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    # 1. Setup Data
    sub = Subject(name="Async Subject")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    topic = Topic(name="Async Topic", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)

    q_data = [QuestionCreate(
        topic_id=topic.id,
        question_text="Async Q",
        question_options=[{"option_text": "A", "value": True}]
    )]
    await create_question(session, q_data)

    # 2. Mock Background Tasks and Keycloak
    with patch("src.routers.exam.BackgroundTasks.add_task") as mock_add_task, \
         patch("src.services.waiting_room.keycloak_client.create_waiting_room_groups", new_callable=AsyncMock) as mock_wr_kc:
        
        mock_wr_kc.return_value = True
        
        payload = {
            "subject_id": sub.id,
            "fraction": 0,
            "exam_title": "Async Exam",
            "topics": ["Async Topic"],
            "number_questions": {"Async Topic": 1},
            "relative_quotations": {"Async Topic": 1.0},
            "num_variations": 1
        }

        response = await client.post("/api/exams/generate_async", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == GenerationStatus.PENDING
        assert "id" in data
        
        # Verify background task was scheduled
        assert mock_add_task.called
        # Check task arguments (task_func, session_factory, config_id, num_vars, specs)
        args, _ = mock_add_task.call_args
        assert args[0] == generate_exams_task
        assert args[2] == data["id"] # config_id
        assert args[3] == 1 # num_variations

@pytest.mark.asyncio
async def test_get_config_status_endpoint(client, mock_auth, session):
    """Test the GET /config/{id}/status endpoint."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Status Subject")
    session.add(sub)
    await session.commit()

    # Create config with specific status
    config = ExamConfig(
        subject_id=sub.id,
        fraction=0,
        status=GenerationStatus.PROCESSING
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    response = await client.get(f"/api/exams/config/{config.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == GenerationStatus.PROCESSING
    assert data["is_ready"] is False

    # Update to COMPLETED
    config.status = GenerationStatus.COMPLETED
    session.add(config)
    await session.commit()

    response = await client.get(f"/api/exams/config/{config.id}/status")
    assert response.json()["status"] == GenerationStatus.COMPLETED
    assert response.json()["is_ready"] is True

@pytest.mark.asyncio
async def test_download_exam_zip_endpoint(client, mock_auth, session):
    """Test the GET /config/{id}/download endpoint."""
    app.dependency_overrides[get_current_user_info] = mock_auth

    sub = Subject(name="Download Subject")
    session.add(sub)
    await session.commit()

    # 1. Test download when not ready
    config = ExamConfig(
        subject_id=sub.id,
        fraction=0,
        status=GenerationStatus.PENDING
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    response = await client.get(f"/api/exams/config/{config.id}/download")
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"]

    # 2. Test download when ready but file missing
    config.status = GenerationStatus.COMPLETED
    config.zip_path = "/non/existent/path.zip"
    session.add(config)
    await session.commit()

    response = await client.get(f"/api/exams/config/{config.id}/download")
    assert response.status_code == 404
    assert "not found on server" in response.json()["detail"]

    # 3. Test successful download
    with patch("src.routers.exam.os.path.exists", return_value=True), \
         patch("src.routers.exam.FileResponse") as mock_file_response:
        
        mock_file_response.return_value = Response(content=b"dummy zip", media_type="application/zip")
        
        response = await client.get(f"/api/exams/config/{config.id}/download")
        assert response.status_code == 200
        assert mock_file_response.called

@pytest.mark.asyncio
async def test_generate_exams_task_logic(session):
    """Test the background task function directly."""
    from src.services.exam import generate_exams_task, generate_exams_to_disk
    
    sub = Subject(name="Task Subject")
    session.add(sub)
    await session.commit()
    
    config = ExamConfig(subject_id=sub.id, fraction=0, status=GenerationStatus.PENDING)
    session.add(config)
    await session.commit()
    await session.refresh(config)
    
    # We need a session factory for the task
    from src.core.db import async_session
    
    # Mock the heavy lifting
    with patch("src.services.exam.generate_exams_to_disk", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (b"zip content", "/tmp/test.zip")
        
        # We manually pass the session because in test environment async_session might not be configured
        # But generate_exams_task uses it internally. Let's mock the session_factory.
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__.return_value = session
        
        await generate_exams_task(
            mock_session_factory,
            config.id,
            1,
            {"exam_name": "Test Task"}
        )
        
        await session.refresh(config)
        assert config.status == GenerationStatus.COMPLETED
        assert config.zip_path == "/tmp/test.zip"

@pytest.mark.asyncio
async def test_generate_exams_task_failure_logic(session):
    """Test the background task function when an error occurs."""
    from src.services.exam import generate_exams_task
    
    sub = Subject(name="Failure Subject")
    session.add(sub)
    await session.commit()
    
    config = ExamConfig(subject_id=sub.id, fraction=0, status=GenerationStatus.PENDING)
    session.add(config)
    await session.commit()
    await session.refresh(config)
    
    # Mock generate_exams_to_disk to raise an exception
    with patch("src.services.exam.generate_exams_to_disk", side_effect=Exception("Simulated Failure")):
        
        mock_session_factory = MagicMock()
        # Ensure every call to the factory returns a context manager that yields our session
        mock_session_factory.return_value.__aenter__.return_value = session
        mock_session_factory.return_value.__aexit__.return_value = None
        
        await generate_exams_task(
            mock_session_factory,
            config.id,
            1,
            {"exam_name": "Test Failure Task"}
        )
        
        await session.refresh(config)
        assert config.status == GenerationStatus.FAILED
        # Check that the factory was called at least twice (once for the main block, once for the failure block)
        assert mock_session_factory.call_count >= 2

