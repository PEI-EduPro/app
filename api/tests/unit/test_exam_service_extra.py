import pytest
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.exam import (
    create_configs, delete_exam_config, get_latest_exam_config_id, 
    build_exam_questions, generate_exams_task, generate_exams_from_configs,
    notify_student
)
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.exam_config import ExamConfig
from src.models.exam import Exam
from src.models.waiting_room import WaitingRoom
from src.models.warning import Warning, WarningType

@pytest.mark.asyncio
async def test_create_configs_with_students(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    t = Topic(name="T", subject_id=sub.id)
    session.add(t)
    await session.commit()
    
    specs = {
        "subject_id": sub.id,
        "topics": [str(t.id)],
        "number_questions": {str(t.id): 0},
        "relative_quotations": {str(t.id): 1.0},
        "fraction": 10
    }
    students = [(123, "Name", "email@e.com")]
    ec, tcs = await create_configs(session, specs, student_tuples=students)
    assert ec.nmec_name_list is not None
    data = json.loads(ec.nmec_name_list)
    assert data["123"]["name"] == "Name"

@pytest.mark.asyncio
async def test_delete_exam_config_full(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, zip_path="/tmp/fake.zip")
    session.add(ec)
    await session.commit()
    
    e = Exam(exam_config_id=ec.id, capture_path="/tmp/cap.jpg")
    session.add(e)
    wr = WaitingRoom(exam_config_id=ec.id)
    session.add(wr)
    w = Warning(exam_config_id=ec.id, type=WarningType.multiple_students_to_exam)
    session.add(w)
    await session.commit()
    
    with patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove, \
         patch("src.services.exam.keycloak_client.delete_waiting_room_groups", new_callable=AsyncMock) as mock_kc:
        
        mock_kc.return_value = True
        result = await delete_exam_config(session, ec.id)
        assert result is True
        assert mock_remove.call_count == 2 # zip and capture
        mock_kc.assert_called_once()
        
        # Verify DB deletion
        assert await session.get(ExamConfig, ec.id) is None

@pytest.mark.asyncio
async def test_get_latest_exam_config_id_fail(session):
    with pytest.raises(ValueError, match="No exam config found"):
        await get_latest_exam_config_id(session, 9999)

def test_build_exam_questions_empty():
    e = Exam(exam_config_id=1)
    assert build_exam_questions(e, 10.0) == []

def test_build_exam_questions_success():
    e = Exam(
        exam_config_id=1,
        results=json.dumps({"0": {"A": True, "B": False}}),
        answer_key={"0": 0},
        relative_weights={"0": 1.0}
    )
    res = build_exam_questions(e, 10.0)
    assert len(res) == 1
    assert res[0]["correct_answer"] == "a"
    assert res[0]["value"] == 20.0

@pytest.fixture
def session_factory(session):
    def factory():
        return session
    return factory

@pytest.mark.asyncio
async def test_generate_exams_task_failure(session_factory):
    with patch("src.services.exam.get_exam_config_by_id", new_callable=AsyncMock) as mock_get:
        ec = MagicMock()
        mock_get.return_value = ec
        with patch("src.services.exam.generate_exams_to_disk", side_effect=Exception("Crash")):
            await generate_exams_task(session_factory, 1, 1, {})
            assert ec.status == "FAILED"

@pytest.mark.asyncio
async def test_generate_exams_from_configs(session):
    ec = ExamConfig(id=1, subject_id=1, fraction=10)
    with patch("src.services.exam.generate_exams_to_disk", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (b"zip", "/path/to.zip")
        # We need to mock session.add and commit because ec is not in session
        with patch.object(session, "add"), patch.object(session, "commit"):
            res = await generate_exams_from_configs(session, ec, [], 1)
            assert res == b"zip"
            assert ec.zip_path == "/path/to.zip"

@pytest.mark.asyncio
async def test_notify_student_success(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, exam_name="Test Exam", fraction=0)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, student_email="s@e.com", student_name="S", nmec=123, results="{}", answer_key={}, relative_weights={}, grade=10.0)
    session.add(e)
    await session.commit()
    
    with patch("src.services.exam.jinja_env.get_template") as mock_get_temp, \
         patch("smtplib.SMTP") as mock_smtp, \
         patch("os.getenv", side_effect=lambda k, d=None: "test@e.com" if k=="SENDER_EMAIL" else "587" if k=="EMAIL_NOTIFIER_PORT" else d):
        
        mock_temp = MagicMock()
        mock_temp.render.return_value = "<html></html>"
        mock_get_temp.return_value = mock_temp
        
        res = await notify_student(session, e, {"exam_capture": False})
        assert res["message"] == "Email enviado com sucesso"

@pytest.mark.asyncio
async def test_notify_student_fail_email(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, exam_name="Test Exam", fraction=0)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, student_email="s@e.com", student_name="S", nmec=123, results="{}", answer_key={}, relative_weights={}, grade=10.0)
    session.add(e)
    await session.commit()
    
    from fastapi import HTTPException
    with patch("src.services.exam.jinja_env.get_template"), \
         patch("smtplib.SMTP", side_effect=Exception("SMTP error")):
        with pytest.raises(HTTPException) as exc:
            await notify_student(session, e, {"exam_capture": False})
        assert exc.value.status_code == 500
