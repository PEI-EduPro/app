from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.db import get_session
from src.core.deps import get_current_user
from src.models.user import User

router = APIRouter()

@router.get("/")
async def read_products(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Your product logic here
    return {"message": "Products endpoint"}