from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.user import User,UserRole

async def get_user_by_keycloak_id(session: AsyncSession, keycloak_id: str) -> User | None:
    result = await session.exec(select(User).where(User.keycloak_id == keycloak_id))
    return result.first()

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.exec(select(User).where(User.email == email))
    return result.first()

async def create_user(
    session: AsyncSession, 
    keycloak_id: str, 
    email: str, 
    name: str, 
    mechanographic_number: str = "696969"
) -> User:
    """Create a new user with the provided details"""
    user = User(
        keycloak_id=keycloak_id,
        email=email,
        name=name,
        mechanographic_number=mechanographic_number,
        role=UserRole.STUDENT # Default role
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user_role(session: AsyncSession, user_id: int, role: UserRole) -> User | None:
    user = await session.get(User, user_id)
    if user:
        user.role = role
        await session.commit()
        await session.refresh(user)
    return user