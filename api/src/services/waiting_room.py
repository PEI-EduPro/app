from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.models.waiting_room import WaitingRoom, WaitingRoomState, WaitingRoomInfoResponse, WaitingRoomMetricsResponse, ProfessorWaitingRoomItem
from src.models.warning import Warning, WarningType
from src.models.exam_config import ExamConfig
from src.models.exam import Exam
from src.models.subject import Subject
from src.services.exam import get_exams_by_config_id
from src.core.keycloak import keycloak_client
from typing import Optional, List, Set, Dict
import json
import logging

logger = logging.getLogger(__name__)

async def get_waiting_room(session: AsyncSession, waiting_room_id: int) -> Optional[WaitingRoom]:
    stmt = select(WaitingRoom).where(WaitingRoom.id == waiting_room_id)
    result = await session.exec(stmt)
    return result.first()

async def update_waiting_room_state(session: AsyncSession, waiting_room_id: int, new_state: WaitingRoomState) -> Optional[WaitingRoom]:
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        return None
    
    waiting_room.state = new_state
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)
    return waiting_room

async def create_waiting_room_service(
    session: AsyncSession,
    exam_config_id: int,
    regent_keycloak_id: str,
    vigilant_keycloak_ids: List[str]
) -> WaitingRoom:
    # Create WaitingRoom in DB
    waiting_room = WaitingRoom(exam_config_id=exam_config_id)
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)

    try:
        # Create Keycloak groups and assign users
        await keycloak_client.create_waiting_room_groups(
            waiting_room_id=waiting_room.id,
            regent_keycloak_id=regent_keycloak_id,
            vigilant_ids=vigilant_keycloak_ids
        )
    except Exception as e:
        # If keycloak fails, we should ideally rollback the DB creation
        await session.delete(waiting_room)
        await session.commit()
        raise e

    return waiting_room

async def get_waiting_room_info_service(session: AsyncSession, waiting_room_id: int) -> Optional[WaitingRoomInfoResponse]:
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        return None
    
    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    if not exam_config:
        return None
        
    exams = await get_exams_by_config_id(session, waiting_room.exam_config_id)
    exam_ids = [exam.id for exam in exams]
    
    student_list = {}
    if exam_config.nmec_name_list:
        try:
            student_list = json.loads(exam_config.nmec_name_list)
        except json.JSONDecodeError:
            pass
            
    return WaitingRoomInfoResponse(
        id=waiting_room.id,
        exam_config_id=waiting_room.exam_config_id,
        state=waiting_room.state,
        associations=waiting_room.associations,
        student_list=student_list,
        exam_ids=exam_ids,
        total_students=len(student_list),
        total_exams=len(exam_ids)
    )

async def associate_student_to_exam_service(
    session: AsyncSession,
    waiting_room_id: int,
    exam_id: int,
    student_nmec: str
) -> Optional[WaitingRoom]:
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        return None
        
    association_string = f"{exam_id}:{student_nmec}"
    
    # We allow adding it even if technically one side might exist according to the TODO rules
    # It will be validated later.
    
    # ensure it's not a duplicate exactly
    if association_string not in waiting_room.associations:
        # Create a new list to ensure SQLAlchemy detects the change to the JSON column
        new_associations = list(waiting_room.associations)
        new_associations.append(association_string)
        waiting_room.associations = new_associations
        session.add(waiting_room)
        await session.commit()
        await session.refresh(waiting_room)
        
    return waiting_room

async def get_waiting_room_metrics_service(
    session: AsyncSession,
    waiting_room_id: int
) -> Optional[WaitingRoomMetricsResponse]:
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        return None
        
    associated_exams = set()
    associated_students = set()
    
    for assoc in waiting_room.associations:
        if ":" in assoc:
            exam_id, student_nmec = assoc.split(":", 1)
            associated_exams.add(exam_id)
            associated_students.add(student_nmec)
            
    return WaitingRoomMetricsResponse(
        associated_exams_count=len(associated_exams),
        associated_students_count=len(associated_students)
    )

async def close_waiting_room_service(session: AsyncSession, waiting_room_id: int) -> WaitingRoom:
    waiting_room = await get_waiting_room(session, waiting_room_id)
    if not waiting_room:
        raise ValueError("Waiting room not found")

    if waiting_room.state not in [WaitingRoomState.RUNNING, WaitingRoomState.CLOSED]:
        raise ValueError("Waiting room must be in running or closed state to be closed.")

    # 1. Update state to CLOSED
    waiting_room.state = WaitingRoomState.CLOSED
    session.add(waiting_room)
    await session.commit()
    await session.refresh(waiting_room)

    # 2. Parse associations
    student_to_exams: Dict[str, Set[int]] = {}
    exam_to_students: Dict[int, Set[str]] = {}
    
    for assoc in waiting_room.associations:
        if ":" in assoc:
            try:
                exam_id_str, student_nmec = assoc.split(":", 1)
                exam_id = int(exam_id_str)
                
                if student_nmec not in student_to_exams:
                    student_to_exams[student_nmec] = set()
                student_to_exams[student_nmec].add(exam_id)
                
                if exam_id not in exam_to_students:
                    exam_to_students[exam_id] = set()
                exam_to_students[exam_id].add(student_nmec)
            except (ValueError, TypeError):
                continue

    # 3. Load nmec-name mapping for warnings
    exam_config = await session.get(ExamConfig, waiting_room.exam_config_id)
    nmec_to_name = {}
    if exam_config and exam_config.nmec_name_list:
        try:
            nmec_to_name = json.loads(exam_config.nmec_name_list)
        except json.JSONDecodeError:
            pass

    def get_nmec_name(nmec_str: str) -> str:
        name = nmec_to_name.get(nmec_str, "Unknown")
        return f"{nmec_str}:{name}"

    # 4. Identify conflicts and create warnings
    conflict_students: Set[str] = set()
    conflict_exams: Set[int] = set()

    # Check for multiple exams per student
    for student_nmec, exams in student_to_exams.items():
        if len(exams) > 1:
            conflict_students.add(student_nmec)
            for e_id in exams:
                conflict_exams.add(e_id)
            
            warning = Warning(
                exam_config_id=waiting_room.exam_config_id,
                type=WarningType.multiple_exams_to_student,
                student_list=get_nmec_name(student_nmec),
                exam_list=list(exams)
            )
            session.add(warning)

    # Check for multiple students per exam
    for exam_id, students in exam_to_students.items():
        if len(students) > 1:
            conflict_exams.add(exam_id)
            for s_nmec in students:
                conflict_students.add(s_nmec)
            
            students_str = "; ".join([get_nmec_name(s) for s in students])
            warning = Warning(
                exam_config_id=waiting_room.exam_config_id,
                type=WarningType.multiple_students_to_exam,
                student_list=students_str,
                exam_list=[exam_id]
            )
            session.add(warning)

    # 5. Map clean associations (1:1 with no conflicts)
    for exam_id, students in exam_to_students.items():
        # Only process if this exam has exactly one student AND that student is not involved in any other conflict
        if len(students) == 1:
            student_nmec = list(students)[0]
            if student_nmec not in conflict_students and exam_id not in conflict_exams:
                exam = await session.get(Exam, exam_id)
                if exam:
                    try:
                        exam.nmec = int(student_nmec)
                        session.add(exam)
                    except (ValueError, TypeError):
                        pass

    await session.commit()
    await session.refresh(waiting_room)

    return waiting_room


async def get_professor_waiting_rooms(
    session: AsyncSession,
    professor_keycloak_id: str,
    professor_groups: List[str]
) -> List[ProfessorWaitingRoomItem]:
    """
    Get all waiting rooms where the professor is either a regent or vigilant.
    
    Uses the professor's Keycloak groups to find associated waiting rooms.
    Groups follow the pattern: w{waiting_room_id}/regent or w{waiting_room_id}/vigilant
    
    Returns a flat list of waiting rooms with subject information:
    [
        {
            "subject_id": 1,
            "subject_name": "Mathematics",
            "waiting_room_id": 5,
            "state": "preparation" | "running" | "closed",
            "role": "regent" | "vigilant"
        },
        ...
    ]
    """
    # Extract waiting room IDs and roles from groups
    waiting_room_ids_with_roles: Dict[int, str] = {}
    
    for group in professor_groups:
        # Keycloak groups often have a leading slash (/w1/regent for example). Remove it.
        group = group.lstrip("/")

        # Check for waiting room groups (pattern: w{id}/role)
        if group.startswith("w") and "/" in group:
            parts = group.split("/", 1)
            if len(parts) == 2:
                wr_prefix, role = parts
                if role in ["regent", "vigilant"]:
                    try:
                        waiting_room_id = int(wr_prefix[1:])  # Remove 'w' prefix
                        waiting_room_ids_with_roles[waiting_room_id] = role
                    except ValueError:
                        logger.warning(f"Invalid waiting room ID in group: {group}")
                        continue
    
    if not waiting_room_ids_with_roles:
        logger.debug("Returning early. No waiting_room_ids were found.")
        return []
    
    # Fetch all waiting rooms at once
    stmt = select(WaitingRoom).where(
        WaitingRoom.id.in_(list(waiting_room_ids_with_roles.keys()))
    )
    results = await session.exec(stmt)
    waiting_rooms = results.all()
    
    result: List[ProfessorWaitingRoomItem] = []
    
    # For each waiting room, get the subject info via ExamConfig
    for wr in waiting_rooms:
        role = waiting_room_ids_with_roles.get(wr.id)
        if not role:
            continue
        
        # Get ExamConfig to find subject_id
        exam_config = await session.get(ExamConfig, wr.exam_config_id)
        if not exam_config:
            logger.warning(f"ExamConfig not found for waiting room {wr.id}")
            continue
        
        # Get Subject to get the name
        subject = await session.get(Subject, exam_config.subject_id)
        if not subject:
            logger.warning(f"Subject not found for exam config {wr.exam_config_id}")
            continue
        
        result.append(ProfessorWaitingRoomItem(
            subject_id=subject.id,
            subject_name=subject.name,
            waiting_room_id=wr.id,
            state=wr.state.value,
            role=role
        ))
    
    return result
