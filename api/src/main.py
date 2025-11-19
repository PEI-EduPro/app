from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.db import create_db_and_tables
from src.core.config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting application initialization...")
    
    # Create database tables
    try:
        logger.info("Creating database tables...")
        await create_db_and_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    
    # Verify database connection
    try:
        from src.core.db import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection verification failed: {str(e)}")
    
    yield
    
    logger.info("Application shutting down...")

app = FastAPI(
    title="Education Platform API",
    description="Backend API with Keycloak authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
from src.routers import user
app.include_router(user.router, prefix="/api/users", tags=["users"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Education Platform API is running"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Education Platform API",
        "documentation": "/docs",
        "health_check": "/health"
    }