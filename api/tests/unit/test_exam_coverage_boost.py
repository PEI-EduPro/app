import pytest
import json
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select, func

from src.services.exam import (
    transition_exam_config_state,
    get_exam_session_info_service,
    associate_student_to_exam_service,
    get_exam_session_metrics_service,
    close_exam_session_service,
    get_professor_exam_sessions,
    correct_by_hand,
    notify_student,
    _get_answers_map,
    _update_rules,
    _write_blank_answers,
    _write_answer_key,
    _write_all_solutions,
    _compile_latex,
    create_configs_and_exams,
    delete_exam_config,
    generate_exams_to_disk,
    generate_exams_task,
    process_student_list_csv,
    store_student_list,
    get_subject_id_by_exam_config_id,
    get_student_list,
    get_exams_by_config_id,
    get_latest_exam_config_id,
    build_exam_questions,
    create_exam_session_groups_service
)
from src.models.exam_config import ExamConfig, ExamState, GenerationStatus
from src.models.exam import Exam
from src.models.subject import Subject
from src.models.topic import Topic
from src.models.topic_config import TopicConfig
from src.models.question import Question

@pytest.fixture
def session_factory(session):
    def factory():
        return session
    return factory

@pytest.mark.asyncio
async def test_transition_exam_config_state(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.PREPARING)
    session.add(ec)
    await session.commit()
    
    updated = await transition_exam_config_state(session, ec.id, ExamState.RUNNING)
    assert updated.state == ExamState.RUNNING
    
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await transition_exam_config_state(session, 9999, ExamState.RUNNING)

@pytest.mark.asyncio
async def test_transition_exam_config_state_validation_fail(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    
    # 1. Validation fail: unresolved warnings
    from src.models.warning import Warning, WarningType
    w = Warning(exam_config_id=ec.id, type=WarningType.multiple_students_to_exam)
    session.add(w)
    await session.commit()
    
    with pytest.raises(ValueError, match="unresolved warnings"):
        await transition_exam_config_state(session, ec.id, ExamState.VALIDATION)
    
    # Clean up warning for next test
    await session.delete(w)
    await session.commit()

    # 2. Validation fail: unvalidated pictured exams
    e = Exam(exam_config_id=ec.id, capture_path="/some/path.jpg", validated=False)
    session.add(e)
    await session.commit()
    
    # Need to make sure the session is clean so the service re-fetches correctly
    ec_id = ec.id
    session.expire_all()
    
    with pytest.raises(ValueError, match="not been validated"):
        await transition_exam_config_state(session, ec_id, ExamState.COMPLETED)

@pytest.mark.asyncio
async def test_create_exam_session_groups_service(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    with patch("src.services.exam.keycloak_client.create_exam_session_groups", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = True
        await create_exam_session_groups_service(session, ec.id, "regent_id", ["vig1"])
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_get_exam_session_info_service(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    # Test not found
    res = await get_exam_session_info_service(session, 9999, [])
    assert res is None
    
    # Test found but no exams
    with pytest.raises(ValueError, match="No exams found"):
        await get_exam_session_info_service(session, ec.id, ["prof_group"])

    # Test found with exams and students
    e = Exam(exam_config_id=ec.id, batch_number=1)
    session.add(e)
    ec.nmec_name_list = json.dumps({"123": {"name": "John"}})
    session.add(ec)
    await session.commit()
    
    res = await get_exam_session_info_service(session, ec.id, [f"w{ec.id}/regent"])
    assert res is not None
    assert res.id == ec.id
    assert res.role == "regent"
    assert len(res.student_list) == 1

@pytest.mark.asyncio
async def test_associate_student_to_exam_service(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, batch_number=1)
    session.add(e)
    await session.commit()
    
    await associate_student_to_exam_service(session, ec.id, e.id, "12345")
    await session.refresh(ec)
    assert f"{e.id}:12345" in ec.associations

@pytest.mark.asyncio
async def test_get_exam_session_metrics_service(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    res = await get_exam_session_metrics_service(session, ec.id)
    assert res.associated_exams_count == 0

@pytest.mark.asyncio
async def test_close_exam_session_service(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.RUNNING)
    session.add(ec)
    await session.commit()
    
    res = await close_exam_session_service(session, ec.id)
    assert res.state == ExamState.WARNING_HANDLING

@pytest.mark.asyncio
async def test_get_professor_exam_sessions(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, state=ExamState.COMPLETED)
    session.add(ec)
    await session.commit()
    
    # Passing groups directly as the function expects them
    groups = [f"w{ec.id}/regent"]
    res = await get_professor_exam_sessions(session, "user_id", groups)
    assert len(res) == 1
    assert res[0].exam_config_id == ec.id
    assert res[0].role == "regent"

@pytest.mark.asyncio
async def test_correct_by_hand_edge_cases(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, fraction=10)
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, answer_key={"0": 0}, relative_weights={"0": 1.0})
    session.add(e)
    await session.commit()
    
    grid = {"0": {"A": True}}
    res = await correct_by_hand(session, e.id, grid)
    assert res.grade == 20.0
    
    grid_wrong = {"0": {"B": True}}
    res = await correct_by_hand(session, e.id, grid_wrong)
    # 20.0 * (10/100) = 2.0 penalty. Score = 0 - 2 = -2. Max(0, -2) = 0
    assert res.grade == 0.0

    with pytest.raises(ValueError, match="Exam not found"):
        await correct_by_hand(session, 9999, {})

@pytest.mark.asyncio
async def test_notify_student_complex(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, exam_name="Test Exam", fraction=10)
    session.add(ec)
    await session.commit()
    # Mocking capture_path to test image attachment
    with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
        tmp.write(b"fake image data")
        tmp.flush()
        
        # Complex results to trigger all template logic
        results = {"0": {"A": True, "B": False}, "1": {"A": False, "C": True}}
        answer_key = {"0": 0, "1": 0} # 0 is A
        relative_weights = {"0": 1.0, "1": 1.0}
        
        e = Exam(exam_config_id=ec.id, student_email="s@e.com", student_name="S", nmec=123, 
                 results=json.dumps(results), answer_key=answer_key, relative_weights=relative_weights, grade=10.0,
                 capture_path=tmp.name)
        session.add(e)
        await session.commit()
        
        with patch("src.services.exam.jinja_env.get_template") as mock_get_temp, \
             patch("smtplib.SMTP") as mock_smtp, \
             patch("os.path.exists", return_value=True), \
             patch("os.getenv", side_effect=lambda k, d=None: "test@e.com" if k=="SENDER_EMAIL" else "587" if k=="EMAIL_NOTIFIER_PORT" else d):
            
            mock_temp = MagicMock()
            mock_temp.render.return_value = "<html></html>"
            mock_get_temp.return_value = mock_temp
            
            # Test with image attachment
            res = await notify_student(session, e, {"exam_capture": True})
            assert res["message"] == "Email enviado com sucesso"

@pytest.mark.asyncio
async def test_generate_exams_to_disk_versions_cache(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    t = Topic(name="T", subject_id=sub.id)
    session.add(t)
    await session.commit()
    q = Question(topic_id=t.id, question_text="Q")
    session.add(q)
    await session.commit()
    
    ec = ExamConfig(subject_id=sub.id, fraction=10)
    session.add(ec)
    await session.commit()
    tc = TopicConfig(exam_config_id=ec.id, topic_id=t.id, num_questions=1, relative_weight=1.0)
    session.add(tc)
    await session.commit()

    # num_versions < total_exams to trigger versions cache hit
    with patch("shutil.which", return_value="/usr/bin/pdflatex"), \
         patch("src.services.exam._compile_latex", return_value=b"pdf_data"):
        
        zip_bytes, zip_path = await generate_exams_to_disk(
            session, ec, [tc], total_exams=2, num_versions=1,
            exam_date="2026-05-17"
        )
        assert zip_bytes is not None
        assert os.path.exists(zip_path)

@pytest.mark.asyncio
async def test_notify_student_no_email(session):
    e = Exam(id=1, student_email=None)
    with pytest.raises(HTTPException) as exc:
        await notify_student(session, e, {})
    assert exc.value.status_code == 422

def test_get_answers_map():
    q1 = MagicMock()
    q1.id = 1
    o1 = MagicMock(value=True)
    o2 = MagicMock(value=False)
    q1.question_options = [o1, o2]
    
    res = _get_answers_map([q1])
    assert 1 in res

@pytest.mark.asyncio
async def test_latex_helpers():
    with tempfile.TemporaryDirectory() as tmpdir:
        # _update_rules
        rules_path = os.path.join(tmpdir, "Rules.tex")
        with open(rules_path, "w") as f:
            f.write("#NUM_QUESTIONS #FRACTION")
        await _update_rules(tmpdir, 10, 0.5)
        with open(rules_path, "r") as f:
            content = f.read()
            assert content == "10 0.5"
        
        # _write_blank_answers
        await _write_blank_answers(tmpdir, 5)
        assert os.path.exists(os.path.join(tmpdir, "T-answers.tex"))
        
        # _write_answer_key
        await _write_answer_key(tmpdir, {1: "A"}, 5)
        assert os.path.exists(os.path.join(tmpdir, "T-answers.tex"))
        
        # _write_all_solutions
        await _write_all_solutions(tmpdir, [("1", {1: "A"})], 5)
        assert os.path.exists(os.path.join(tmpdir, "solutions.tex"))

@pytest.mark.asyncio
async def test_generate_exams_task_success(session_factory, session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, status=GenerationStatus.PENDING)
    session.add(ec)
    await session.commit()
    t = Topic(name="T", subject_id=sub.id)
    session.add(t)
    await session.commit()
    tc = TopicConfig(exam_config_id=ec.id, topic_id=t.id, num_questions=0, relative_weight=1.0)
    session.add(tc)
    await session.commit()
    
    with patch("src.services.exam.generate_exams_to_disk", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (b"zip", "/fake/path.zip")
        await generate_exams_task(session_factory, ec.id, 1, {"exam_name": "Test"})
        
        # Refetch from DB to avoid session issues
        updated_ec = await session.get(ExamConfig, ec.id)
        assert updated_ec.status == GenerationStatus.COMPLETED
        assert updated_ec.zip_path == "/fake/path.zip"

@pytest.mark.asyncio
async def test_generate_exams_task_failure(session_factory, session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, status=GenerationStatus.PENDING)
    session.add(ec)
    await session.commit()
    
    with patch("src.services.exam.generate_exams_to_disk", side_effect=Exception("Crash")):
        await generate_exams_task(session_factory, ec.id, 1, {})
        updated_ec = await session.get(ExamConfig, ec.id)
        assert updated_ec.status == GenerationStatus.FAILED

@pytest.mark.asyncio
async def test_create_configs_validation_fail(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    t = Topic(name="T", subject_id=sub.id)
    session.add(t)
    await session.commit()
    # 0 questions in DB, request 1
    specs = {
        "subject_id": sub.id,
        "topics": [str(t.id)],
        "number_questions": {str(t.id): 1},
        "relative_quotations": {str(t.id): 1.0},
        "fraction": 10
    }
    from src.services.exam import create_configs
    with pytest.raises(ValueError, match="has only 0 questions"):
        await create_configs(session, specs)

@pytest.mark.asyncio
async def test_process_student_list_csv(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    csv_content = b"nmec,name,email\n123,John,john@e.com"
    await process_student_list_csv(session, ec.id, csv_content)
    await session.refresh(ec)
    data = json.loads(ec.nmec_name_list)
    assert data["123"]["name"] == "John"

@pytest.mark.asyncio
async def test_store_student_list_fail(session):
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await store_student_list(session, 9999, "{}")

@pytest.mark.asyncio
async def test_get_subject_id_by_exam_config_id(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    sid = await get_subject_id_by_exam_config_id(ec.id, session)
    assert sid == sub.id
    
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await get_subject_id_by_exam_config_id(9999, session)

@pytest.mark.asyncio
async def test_get_student_list(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, nmec_name_list="some list")
    session.add(ec)
    await session.commit()
    
    res = await get_student_list(session, ec.id)
    assert res == "some list"
    
    with pytest.raises(ValueError, match="Exam configuration not found"):
        await get_student_list(session, 9999)

@pytest.mark.asyncio
async def test_get_exams_by_config_id_fail(session):
    with pytest.raises(ValueError, match="No exams found"):
        await get_exams_by_config_id(session, 9999)

@pytest.mark.asyncio
async def test_get_latest_exam_config_id_success(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id)
    session.add(ec)
    await session.commit()
    
    res = await get_latest_exam_config_id(session, sub.id)
    assert res == ec.id

def test_build_exam_questions_success():
    results = {"0": {"A": True}}
    answer_key = {"0": 0}
    relative_weights = {"0": 1.0}
    e = Exam(exam_config_id=1, results=json.dumps(results), answer_key=answer_key, relative_weights=relative_weights)
    res = build_exam_questions(e, 10.0)
    assert len(res) == 1
    assert res[0]["question_number"] == 0

@pytest.mark.asyncio
async def test_compile_latex_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        main_file = "main.tex"
        with open(os.path.join(tmpdir, main_file), "w") as f:
            f.write("\\newcommand\\tttnumber{0}\\newcommand\\qrcodecontent{0}Exame Época Normal")
        
        # Mock anyio.run_process to succeed and create a PDF
        async def side_effect(*args, **kwargs):
            pdf_path = os.path.join(tmpdir, "main.pdf")
            with open(pdf_path, "wb") as f:
                f.write(b"fake pdf")
            return MagicMock()

        with patch("anyio.run_process", side_effect=side_effect):
            res = await _compile_latex(tmpdir, main_file, 1, subject_name="Math", exam_title="Final", semester="1", academic_year="2025")
            assert res == b"fake pdf"

@pytest.mark.asyncio
async def test_compile_latex_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        main_file = "main.tex"
        with open(os.path.join(tmpdir, main_file), "w") as f:
            f.write("\\newcommand\\tttnumber{0}\\newcommand\\qrcodecontent{0}Exame Época Normal")
        
        # Mock anyio.run_process to fail
        with patch("anyio.run_process", side_effect=Exception("Fail")):
            res = await _compile_latex(tmpdir, main_file, 1)
            assert res is None

@pytest.mark.asyncio
async def test_create_configs_and_exams(session):
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
    
    with patch("src.services.exam.generate_exams_from_configs", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = b"zip"
        res = await create_configs_and_exams(session, specs, num_versions=1)
        assert res == b"zip"

@pytest.mark.asyncio
async def test_delete_exam_config_error_handling(session):
    sub = Subject(name="Sub")
    session.add(sub)
    await session.commit()
    ec = ExamConfig(subject_id=sub.id, zip_path="/non/existent/path.zip")
    session.add(ec)
    await session.commit()
    e = Exam(exam_config_id=ec.id, capture_path="/non/existent/cap.jpg")
    session.add(e)
    await session.commit()
    
    with patch("os.path.exists", return_value=True), \
         patch("os.remove", side_effect=Exception("Perm error")), \
         patch("src.services.exam.keycloak_client.delete_exam_session_groups", new_callable=AsyncMock) as mock_kc:
        
        mock_kc.return_value = False # Force "Failed to delete Keycloak groups" log
        result = await delete_exam_config(session, ec.id)
        assert result is True # Still returns True because it tries its best
