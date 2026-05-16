import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import select
from src.services.subject import (
    create_subject_service,
    get_subjects_for_user,
    update_subject_service,
    delete_subject_service,
    get_students_service,
    get_professors_service,
    get_regent_service,
    add_students_service,
    manage_professor_service,
    remove_professor_service,
    get_all_subjects,
    get_topics_questions_and_options_by_subject_id,
    get_all_subject_topics,
    get_topics_from_subject
)
from src.models.subject import Subject, SubjectUpdate
from src.models.topic import Topic
from src.models.question import Question
from src.models.question_option import QuestionOption

@pytest.mark.asyncio
async def test_create_subject_service_full(session, mock_keycloak, mock_verify_regent):
    # Test success with students and professors (Hits lines 55, 61)
    result = await create_subject_service(
        session, "Full Subject", "regent-123", 
        student_keycloak_ids=["s1"], 
        professor_keycloak_ids=["p1"]
    )
    assert result["subject"].name == "Full Subject"
    assert mock_keycloak.add_students_to_subject.called
    assert mock_keycloak.add_professors_to_subject.called

    # Test failure in Keycloak group creation (Hits line 51)
    mock_keycloak.create_subject_groups_and_assign_regent.return_value = False
    with pytest.raises(RuntimeError, match="Subject creation failed due to a Keycloak error."):
        await create_subject_service(session, "Fail KC Group", "regent-123")

    # Test generic exception and rollback (Hits lines 67-71)
    mock_keycloak.create_subject_groups_and_assign_regent.side_effect = Exception("General Error")
    mock_keycloak.create_subject_groups_and_assign_regent.return_value = None # Reset return value just in case
    with pytest.raises(RuntimeError, match="Subject creation failed due to a Keycloak error."):
        await create_subject_service(session, "Fail Rollback", "regent-123")
    
    # Check rollback
    stmt = select(Subject).where(Subject.name == "Fail Rollback")
    res = await session.exec(stmt)
    assert res.one_or_none() is None

@pytest.mark.asyncio
async def test_get_subjects_for_user_all_paths(session):
    # Manager (Hits line 96)
    user_info = MagicMock()
    user_info.realm_roles = ["manager"]
    user_info.groups = []
    session.add(Subject(name="S1"))
    await session.commit()
    res = await get_subjects_for_user(session, user_info)
    assert len(res) >= 1

    # Student/Professor with groups (Hits lines 102-119)
    user_info.realm_roles = ["student"]
    user_info.groups = ["/s1/students", "/s2/professors", "/s3/regent", "/invalid", "/sx/students"]
    # We need to make sure the IDs match the group paths
    s1 = Subject(id=10, name="S10")
    s2 = Subject(id=20, name="S20")
    s3 = Subject(id=30, name="S30")
    user_info.groups = ["/s10/students", "/s20/professors", "/s30/regent", "/invalid", "/sx/students"]
    session.add(s1)
    session.add(s2)
    session.add(s3)
    await session.commit()
    res = await get_subjects_for_user(session, user_info)
    ids = [s.id for s in res]
    assert 10 in ids
    assert 20 in ids
    assert 30 in ids
    
    # No allowed subjects
    user_info.groups = []
    res = await get_subjects_for_user(session, user_info)
    assert res == []

@pytest.mark.asyncio
async def test_update_subject_service_errors(session, mock_keycloak, mock_verify_regent):
    # Not found
    with pytest.raises(ValueError, match="Subject not found"):
        await update_subject_service(session, 99999, SubjectUpdate())

    # Keycloak failure (Hits line 142)
    sub = Subject(name="S1")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    mock_keycloak.update_subject_regent.return_value = False
    with pytest.raises(RuntimeError, match="Failed to update regent in Keycloak"):
        await update_subject_service(session, sub.id, SubjectUpdate(regent_keycloak_id="r2"))

    # Update students and professors
    await update_subject_service(session, sub.id, SubjectUpdate(student_keycloak_ids=["s2"], professor_keycloak_ids=["p2"]))
    assert mock_keycloak.replace_subject_students.called
    assert mock_keycloak.replace_subject_professors.called

@pytest.mark.asyncio
async def test_delete_subject_service_kc_fail(session, mock_keycloak):
    sub = Subject(name="S1")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    # Hits line 171
    mock_keycloak.delete_subject_groups.return_value = False
    # Should still succeed but log warning
    await delete_subject_service(session, sub.id)
    assert (await session.get(Subject, sub.id)) is None

@pytest.mark.asyncio
async def test_simple_services(session, mock_keycloak, mock_verify_regent):
    sub = Subject(name="S1")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    # get_students_service (Hits 188-192)
    mock_keycloak.get_subject_students.return_value = [{"id": "s1"}]
    res = await get_students_service(session, sub.id)
    assert res == [{"id": "s1"}]
    with pytest.raises(ValueError, match="Subject not found"):
        await get_students_service(session, 99999)

    # get_professors_service (Hits 195-197)
    mock_keycloak.get_subject_professors.return_value = [{"id": "p1"}]
    res = await get_professors_service(session, sub.id)
    assert res == [{"id": "p1"}]
    with pytest.raises(ValueError, match="Subject not found"):
        await get_professors_service(session, 99999)

    # get_regent_service (Hits 201)
    mock_keycloak.get_subject_regent.return_value = {"id": "r1"}
    res = await get_regent_service(session, sub.id)
    assert res == {"id": "r1"}
    with pytest.raises(ValueError, match="Subject not found"):
        await get_regent_service(session, 99999)

    # add_students_service (Hits 205-208)
    await add_students_service(session, sub.id, ["s1"])
    assert mock_keycloak.add_students_to_subject.called
    with pytest.raises(ValueError, match="Subject not found"):
        await add_students_service(session, 99999, [])

    # manage_professor_service (Hits 220-225)
    await manage_professor_service(session, sub.id, "p1", {"perm": True}, is_update=True)
    assert mock_keycloak.manage_professor_permissions.called
    with pytest.raises(ValueError, match="Subject not found"):
        await manage_professor_service(session, 99999, "p1", {})

    # remove_professor_service (Hits 232-240)
    mock_keycloak.remove_professor_from_subject.return_value = True
    await remove_professor_service(session, sub.id, "p1")
    
    mock_keycloak.remove_professor_from_subject.return_value = False
    with pytest.raises(RuntimeError, match="Failed to remove professor from Keycloak"):
        await remove_professor_service(session, sub.id, "p1")
    with pytest.raises(ValueError, match="Subject not found"):
        await remove_professor_service(session, 99999, "p1")

@pytest.mark.asyncio
async def test_read_services(session):
    sub = Subject(name="S1")
    session.add(sub)
    await session.commit()
    
    # get_all_subjects (Hits 250-251)
    res = await get_all_subjects(session)
    assert len(res) >= 1

    # get_topics_from_subject (Hits 322-323)
    session.add(Topic(name="T1", subject_id=sub.id))
    await session.commit()
    res = await get_topics_from_subject(session, sub.id)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_complex_queries(session):
    # get_topics_questions_and_options_by_subject_id (Hits 259-306)
    sub = Subject(name="Math")
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    
    topic = Topic(name="Algebra", subject_id=sub.id)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    
    q = Question(question_text="1+1?", topic_id=topic.id)
    session.add(q)
    await session.commit()
    await session.refresh(q)
    
    opt1 = QuestionOption(option_text="2", value=True, question_id=q.id)
    opt2 = QuestionOption(option_text="3", value=False, question_id=q.id)
    session.add(opt1)
    session.add(opt2)
    await session.commit()
    
    res = await get_topics_questions_and_options_by_subject_id(session, sub.id)
    assert res["subject_name"] == "Math"
    assert topic.id in res["subject_topics"]
    assert q.id in res["subject_topics"][topic.id]["topic_questions"]
    assert res["subject_topics"][topic.id]["topic_questions"][q.id]["answer"] == opt1.id

    # Not found
    res_nf = await get_topics_questions_and_options_by_subject_id(session, 99999)
    assert res_nf == {}

    # get_all_subject_topics (Hits 309-318)
    res_topics = await get_all_subject_topics(session, sub.id)
    assert len(res_topics) == 1
    assert res_topics[0][0].name == "Algebra"
    assert res_topics[0][1] == 1 # 1 question
