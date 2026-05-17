import pytest
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from src.services.exam import notify_student
from src.models.exam import Exam
from src.models.exam_config import ExamConfig
from src.models.subject import Subject
from fastapi import HTTPException


@pytest.fixture
def mock_subject():
    return Subject(name="Mathematics")


@pytest.fixture
def mock_exam_config(mock_subject):
    return ExamConfig(
        subject_id=mock_subject.id,
        fraction=25.0,
        exam_name="Final Exam"
    )


@pytest.fixture
def mock_exam_with_results(mock_exam_config):
    return Exam(
        exam_config_id=mock_exam_config.id,
        student_name="John Doe",
        student_email="john@example.com",
        nmec="12345",
        grade=15.5,
        capture_path="/path/to/capture.jpg",
        results=json.dumps({
            "0": {"A": True, "B": False, "C": False, "D": False},
            "1": {"A": False, "B": True, "C": False, "D": False},
            "2": {"A": False, "B": False, "C": True, "D": False}
        }),
        answer_key={"0": 0, "1": 1, "2": 2},
        relative_weights={"0": 1.0, "1": 1.5, "2": 2.0}
    )


@pytest.fixture
def mock_exam_no_capture(mock_exam_config):
    return Exam(
        exam_config_id=mock_exam_config.id,
        student_name="Jane Smith",
        student_email="jane@example.com",
        nmec="67890",
        grade=12.0,
        capture_path=None,
        results=json.dumps({
            "0": {"A": True, "B": False, "C": False, "D": False},
            "1": {"A": False, "B": False, "C": True, "D": False}
        }),
        answer_key={"0": 0, "1": 1},
        relative_weights={"0": 1.0, "1": 1.0}
    )


@pytest.fixture
def email_options_all_enabled():
    return {
        "exam_capture": True,
        "question_weights": True,
        "red_green_cross_table": True,
        "cumulative_score_table": True,
        "custom_description": "Custom message for students"
    }


@pytest.fixture
def email_options_minimal():
    return {
        "exam_capture": False,
        "question_weights": False,
        "red_green_cross_table": False,
        "cumulative_score_table": False,
        "custom_description": ""
    }


@pytest.mark.asyncio
async def test_notify_student_success(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_all_enabled):
    """Test successful email notification with all options enabled"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv, \
         patch("builtins.open", mock_open(read_data=b"fake_image_data")):
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = await notify_student(session, mock_exam_with_results, email_options_all_enabled)
        
        assert result == {"message": "Email enviado com sucesso"}
        mock_get_config.assert_called_once_with(session, mock_exam_config.id)
        mock_template.assert_called_once_with('email_to_student.html')
        mock_server.starttls.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()


@pytest.mark.asyncio
async def test_notify_student_no_capture(session, mock_subject, mock_exam_config, mock_exam_no_capture, email_options_minimal):
    """Test email notification without capture image"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_no_capture.exam_config_id = mock_exam_config.id
    session.add(mock_exam_no_capture)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv:
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = await notify_student(session, mock_exam_no_capture, email_options_minimal)
        
        assert result == {"message": "Email enviado com sucesso"}
        mock_server.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_notify_student_exam_not_found(session, email_options_minimal):
    """Test notification fails when exam is None"""
    with pytest.raises(HTTPException) as exc_info:
        await notify_student(session, None, email_options_minimal)
    
    assert exc_info.value.status_code == 404
    assert "Exam not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_notify_student_smtp_failure(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_minimal):
    """Test email notification handles SMTP failures"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv:
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("SMTP connection failed")
        mock_smtp.return_value = mock_server
        
        with pytest.raises(HTTPException) as exc_info:
            await notify_student(session, mock_exam_with_results, email_options_minimal)
        
        assert exc_info.value.status_code == 500
        assert "Falha no servidor de email" in exc_info.value.detail


@pytest.mark.asyncio
async def test_notify_student_template_rendering(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_all_enabled):
    """Test that template is rendered with correct data"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv, \
         patch("src.services.exam.os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=b"fake_image_data")):
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        await notify_student(session, mock_exam_with_results, email_options_all_enabled)
        
        render_call_args = mock_html_template.render.call_args[1]
        assert render_call_args["options"] == email_options_all_enabled
        assert render_call_args["student_name"] == "John Doe"
        assert render_call_args["nmec"] == "12345"
        assert render_call_args["grade"] == 15.5
        assert render_call_args["has_capture"] is True
        assert render_call_args["fraction"] == 25.0


@pytest.mark.asyncio
async def test_notify_student_answer_grid_calculation(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_all_enabled):
    """Test that answer grid is correctly calculated"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv, \
         patch("builtins.open", mock_open(read_data=b"fake_image_data")):
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        await notify_student(session, mock_exam_with_results, email_options_all_enabled)
        
        render_call_args = mock_html_template.render.call_args[1]
        answer_grid = render_call_args["answer_grid"]
        
        # Check grid structure
        assert len(answer_grid) == 4  # A, B, C, D rows
        assert answer_grid[0]["label"] == "A"
        assert len(answer_grid[0]["cells"]) == 3  # 3 questions
        
        # Question 0: A is correct and selected -> bg-green
        assert answer_grid[0]["cells"][0]["is_selected"] is True
        assert answer_grid[0]["cells"][0]["bg_class"] == "bg-green"
        
        # Question 1: B is correct and selected -> bg-green
        assert answer_grid[1]["cells"][1]["is_selected"] is True
        assert answer_grid[1]["cells"][1]["bg_class"] == "bg-green"


@pytest.mark.asyncio
async def test_notify_student_score_calculation(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_all_enabled):
    """Test that score details are correctly calculated"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv, \
         patch("builtins.open", mock_open(read_data=b"fake_image_data")):
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        await notify_student(session, mock_exam_with_results, email_options_all_enabled)
        
        render_call_args = mock_html_template.render.call_args[1]
        score_details = render_call_args["score_details"]
        
        # Check score details structure
        assert len(score_details) == 3  # 3 questions
        assert score_details[0]["num"] == "01"
        assert score_details[0]["correct"] == 1
        assert score_details[0]["incorrect"] == 0
        assert "cumulative" in score_details[0]


@pytest.mark.asyncio
async def test_notify_student_email_subject_format(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_minimal):
    """Test that email subject is correctly formatted"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv:
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        await notify_student(session, mock_exam_with_results, email_options_minimal)
        
        # Check that send_message was called
        call_args = mock_server.send_message.call_args[0][0]
        assert call_args['Subject'] == "Nota de Final Exam de Mathematics"
        assert call_args['To'] == "john@example.com"


@pytest.mark.asyncio
async def test_notify_student_missing_capture_file(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_all_enabled):
    """Test notification when capture path exists but file doesn't"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv, \
         patch("os.path.exists", return_value=False):
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        await notify_student(session, mock_exam_with_results, email_options_all_enabled)
        
        # Should still send email successfully, just without capture
        render_call_args = mock_html_template.render.call_args[1]
        assert render_call_args["has_capture"] is False
        mock_server.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_notify_student_attachment_read_error(session, mock_subject, mock_exam_config, mock_exam_with_results, email_options_all_enabled):
    """Test notification handles file read errors for attachments gracefully"""
    session.add(mock_subject)
    await session.commit()
    await session.refresh(mock_subject)
    
    mock_exam_config.subject_id = mock_subject.id
    session.add(mock_exam_config)
    await session.commit()
    await session.refresh(mock_exam_config)
    
    mock_exam_with_results.exam_config_id = mock_exam_config.id
    session.add(mock_exam_with_results)
    await session.commit()
    
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get_config, \
         patch.object(session, "get", new_callable=AsyncMock) as mock_session_get, \
         patch("src.services.exam.jinja_env.get_template") as mock_template, \
         patch("src.services.exam.smtplib.SMTP") as mock_smtp, \
         patch("src.services.exam.os.getenv") as mock_getenv, \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=IOError("Could not read file")):
        
        mock_getenv.side_effect = lambda key, default=None: {
            "SENDER_EMAIL": "test@example.com",
            "EMAIL_NOTIFIER_PORT": "587",
            "EMAIL_CODE": "test_password"
        }.get(key, default)
        
        mock_get_config.return_value = mock_exam_config
        mock_session_get.return_value = mock_subject
        
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html>Test Email</html>"
        mock_template.return_value = mock_html_template
        
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Should not raise exception, but log and continue
        result = await notify_student(session, mock_exam_with_results, email_options_all_enabled)
        assert result == {"message": "Email enviado com sucesso"}
        mock_server.send_message.assert_called_once()
