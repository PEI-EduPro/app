from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.models.waiting_room import WaitingRoom, WaitingRoomState
from typing import Optional

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
