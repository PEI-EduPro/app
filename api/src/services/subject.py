import logging
from typing import List, Optional, Tuple, Set
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.question_option import QuestionOption
from src.models.question import Question
from src.models.topic import Topic, TopicPublic
from src.models.subject import Subject, SubjectUpdate
from src.core.keycloak import keycloak_client
from src.core.deps import verify_regent_exists
from src.services import exam as exam_service
from src.models.exam_config import ExamConfig


logger = logging.getLogger(__name__)

# --- Authenticated Services ---

async def create_subject_service(
    session: AsyncSession,
    name: str,
    regent_keycloak_id: str,
    student_keycloak_ids: List[str] = [],
    professor_keycloak_ids: List[str] = []
) -> dict:
    """
    Orchestrates the creation of a subject:
    1. Verifies regent exists in Keycloak.
    2. Creates Subject in Postgres.
    3. Creates Groups in Keycloak.
    4. Adds students and professors to groups.
    """
    # 1. Verify regent
    regent_info = await verify_regent_exists(regent_keycloak_id)
    
    # 2. DB Creation
    db_subject = Subject(name=name)
    session.add(db_subject)
    await session.commit()
    await session.refresh(db_subject)
    logger.info(f"Subject '{db_subject.name}' created in DB with ID: {db_subject.id}")
    
    # 3. Keycloak Group Creation
    try:
        success = await keycloak_client.create_subject_groups_and_assign_regent(
            subject_id=str(db_subject.id),
            regent_keycloak_id=regent_keycloak_id
        )
        if not success:
            raise RuntimeError("Keycloak group creation returned false.")
        
        # 4. Add students and professors
        if student_keycloak_ids:
            await keycloak_client.add_students_to_subject(
                subject_id=str(db_subject.id),
                student_ids=student_keycloak_ids
            )
        
        if professor_keycloak_ids:
            await keycloak_client.add_professors_to_subject(
                subject_id=str(db_subject.id),
                professor_ids=professor_keycloak_ids
            )
            
    except Exception as e:
        logger.error(f"Failed to create Keycloak groups for subject {db_subject.id}: {e}")
        # Rollback DB creation if Keycloak fails to ensure consistency
        await session.delete(db_subject)
        await session.commit()
        raise RuntimeError(f"Subject created in DB, but Keycloak group creation failed: {e}")

    return {
        "subject": db_subject,
        "regent_username": regent_info.get('username')
    }

async def get_subjects_for_user(
    session: AsyncSession,
    user_info: dict
) -> List[Subject]:
    """
    Returns subjects based on user role.
    Manager -> All.
    Others -> Only subjects found in their Keycloak groups.
    """
    user_roles = user_info.realm_roles
    user_groups = user_info.groups
    
    # 1. Manager Access
    if "manager" in user_roles:
        result = await session.exec(select(Subject))
        return list(result.all())
    
    # 2. Filtered Access
    allowed_subject_ids: Set[int] = set()
    relevant_subgroups = {"regent", "professors", "students"}
    
    for group_path in user_groups:
        # Expected: /s{id}/{role}
        clean_path = group_path.lstrip('/')
        parts = clean_path.split('/')
        
        if len(parts) == 2:
            subject_part = parts[0]
            role_part = parts[1]
            if subject_part.startswith('s') and role_part in relevant_subgroups:
                try:
                    subject_id = int(subject_part[1:])
                    allowed_subject_ids.add(subject_id)
                except ValueError:
                    continue
                    
    if not allowed_subject_ids:
        return []
        
    statement = select(Subject).where(Subject.id.in_(allowed_subject_ids))
    result = await session.exec(statement)
    return list(result.all())

async def update_subject_service(
    session: AsyncSession,
    subject_id: int,
    subject_update: SubjectUpdate
) -> Subject:
    subject = await get_subject_by_id(session, subject_id)
    if not subject:
        raise ValueError("Subject not found")
        
    # Update Name
    if subject_update.name:
        subject.name = subject_update.name
        
    # Update Regent (Keycloak Interaction)
    if subject_update.regent_keycloak_id:
        await verify_regent_exists(subject_update.regent_keycloak_id)
        success = await keycloak_client.update_subject_regent(
            subject_id=str(subject_id),
            new_regent_id=subject_update.regent_keycloak_id
        )
        if not success:
            raise RuntimeError("Failed to update regent in Keycloak")
    
    # Update Students
    if subject_update.student_keycloak_ids is not None:
        await keycloak_client.replace_subject_students(
            subject_id=str(subject_id),
            student_ids=subject_update.student_keycloak_ids
        )
    
    # Update Professors
    if subject_update.professor_keycloak_ids is not None:
        await keycloak_client.replace_subject_professors(
            subject_id=str(subject_id),
            professor_ids=subject_update.professor_keycloak_ids
        )
            
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject

async def delete_subject_service(session: AsyncSession, subject_id: int):
    subject = await get_subject_by_id(session, subject_id)
    if not subject:
        raise ValueError("Subject not found")
        
    # 1. Delete Keycloak Groups for the subject
    kc_success = await keycloak_client.delete_subject_groups(str(subject_id))
    if not kc_success:
        logger.warning(f"Keycloak cleanup failed for subject {subject_id}")

    # 2. Use the improved exam deletion service for all related exam configurations.
    # This handles exams, files, waiting rooms, warnings, and Keycloak groups.   
    result = await session.exec(select(ExamConfig).where(ExamConfig.subject_id == subject_id))
    exam_configs = result.all()
    for ec in exam_configs:
        await exam_service.delete_exam_config(session, ec.id)

    # 3. Delete DB Subject
    # This cascades to Topics, Questions, Options, and any remaining related data via SQLModel relationships
    await session.delete(subject)
    await session.commit()
    logger.info(f"Successfully deleted subject {subject_id} and all related data.")

async def get_students_service(session: AsyncSession, subject_id: int) -> List[dict]:
    # Check DB existence
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    
    # Fetch from Keycloak
    return await keycloak_client.get_subject_students(str(subject_id))

async def get_professors_service(session: AsyncSession, subject_id: int) -> List[dict]:
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    return await keycloak_client.get_subject_professors(str(subject_id))

async def get_regent_service(session: AsyncSession, subject_id: int) -> dict:
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    return await keycloak_client.get_subject_regent(str(subject_id))

async def add_students_service(session: AsyncSession, subject_id: int, student_ids: List[str]):
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    
    await keycloak_client.add_students_to_subject(
        subject_id=str(subject_id), 
        student_ids=student_ids
    )

async def manage_professor_service(
    session: AsyncSession, 
    subject_id: int, 
    professor_id: str, 
    permissions: dict,
    is_update: bool = False
):
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    if not is_update:
        # Check existence if adding new
        await verify_regent_exists(professor_id)
    await keycloak_client.manage_professor_permissions(
        subject_id=str(subject_id),
        professor_id=professor_id,
        permissions=permissions
    )

async def remove_professor_service(session: AsyncSession, subject_id: int, professor_id: str):
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    success = await keycloak_client.remove_professor_from_subject(
        subject_id=str(subject_id),
        professor_id=professor_id
    )
    if not success:
        raise RuntimeError("Failed to remove professor from Keycloak")
    return True

# --- Helpers / Read-Only ---

async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Optional[Subject]:
    """Get subject by ID."""
    return await session.get(Subject, subject_id)

async def get_all_subjects(session: AsyncSession) -> List[Subject]:
    """Get all subjects (Admin/Internal use)."""
    result = await session.exec(select(Subject))
    return list(result.all())

# --- Existing Complex Queries ---

async def get_topics_questions_and_options_by_subject_id(
    session: AsyncSession, subject_id: int
) -> dict:
    #não tocar nesta query, está bem cozinhada
    stmt = (
        select(Subject)
        .where(Subject.id == subject_id)
        .options(
            joinedload(Subject.topics)
                .joinedload(Topic.questions)
                .joinedload(Question.question_options)
        )
    )

    result = await session.exec(stmt)
    subject: Subject | None = result.unique().one_or_none()

    if not subject:
        return {}

    result_subject = {
        "subject_name": subject.name,
        "subject_id":subject.id,
        "subject_topics": {}
    }

    for topic in subject.topics:
        topic_data = {
            "topic_name": topic.name,
            "topic_id":topic.id,
            "topic_questions": {}
        }

        for question in topic.questions:
            question_data = {
                "question_text": question.question_text,
                "question_id":question.id,
                "question_options": {},
                "answer" : ""
            }

            for option in question.question_options:
                question_data["question_options"][option.id] = option.option_text

                if option.value:
                    question_data["answer"] = option.id

            topic_data["topic_questions"][question.id] = question_data

        result_subject["subject_topics"][topic.id] = topic_data

    return result_subject

async def get_all_subject_topics(session: AsyncSession, subject_id: int) -> List[Tuple[TopicPublic, int]]:
    topics_result = await session.exec(select(Topic).where(Topic.subject_id == subject_id))
    topics = topics_result.all()
    
    result = []
    for topic in topics:
        questions_result = await session.exec(select(Question).where(Question.topic_id == topic.id))
        count = len(questions_result.all())
        result.append((TopicPublic.model_validate(topic), count))
    
    return result

async def get_topics_from_subject(session: AsyncSession, subject_id: int) -> List[Topic]:
    """Get all topics from a subject."""
    result = await session.exec(select(Topic).where(Topic.subject_id == subject_id))
    return list(result.all())
