from sqlmodel import create_engine, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from src.core.settings import settings

# Create async engine
engine = create_async_engine(
    str(settings.PGSQL_DATABASE_URI).replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,  # Set to False in production
    future=True
)

# Create sessionmaker
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """Dependency to get async database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def create_db_and_tables():
    """Create all database tables (for lifespan event)"""
    await init_db()