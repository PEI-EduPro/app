from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.models.waiting_room import WaitingRoom, WaitingRoomState, WaitingRoomInfoResponse, WaitingRoomMetricsResponse
from src.models.exam_config import ExamConfig
from src.services.exam import get_exams_by_config_id
from src.core.keycloak import keycloak_client
from typing import Optional, List
import json

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
