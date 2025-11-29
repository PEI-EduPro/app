import logging
from typing import List, Optional, Set
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.subject import Subject, SubjectUpdate
from src.core.keycloak import keycloak_client

from src.core.deps import verify_regent_exists

logger = logging.getLogger(__name__)

async def create_subject_service(
    session: AsyncSession,
    name: str,
    regent_keycloak_id: str
) -> dict:
    """
    Orchestrates the creation of a subject:
    1. Verifies regent exists in Keycloak.
    2. Creates Subject in Postgres.
    3. Creates Groups in Keycloak.
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
    success = await keycloak_client.create_subject_groups_and_assign_regent(
        subject_id=str(db_subject.id),
        regent_keycloak_id=regent_keycloak_id
    )

    if not success:
        logger.error(f"Failed to create Keycloak groups for subject {db_subject.id}.")
        # Optional: Implement DB rollback logic here if strict consistency is needed
        raise RuntimeError("Subject created in DB, but Keycloak group creation failed.")

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
    username = user_info.username

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

async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Optional[Subject]:
    return await session.get(Subject, subject_id)

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

    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject

async def delete_subject_service(session: AsyncSession, subject_id: int):
    subject = await get_subject_by_id(session, subject_id)
    if not subject:
        raise ValueError("Subject not found")

    # Delete Keycloak Groups
    kc_success = await keycloak_client.delete_subject_groups(str(subject_id))
    if not kc_success:
        logger.warning(f"Keycloak cleanup failed for subject {subject_id}")

    # Delete DB
    await session.delete(subject)
    await session.commit()

async def get_students_service(session: AsyncSession, subject_id: int) -> List[dict]:
    # Check DB existence
    if not await get_subject_by_id(session, subject_id):
        raise ValueError("Subject not found")
    
    # Fetch from Keycloak
    return await keycloak_client.get_subject_students(str(subject_id))

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