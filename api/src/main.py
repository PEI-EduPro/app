from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
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
    lifespan=lifespan,
    root_path="/api"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "https://localhost",
        "https://mednat.ieeta.pt:9042",
        "https://bioinformatics.ua.pt",
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routers
from src.routers import user, subject, topic, question, question_option, exam, warning
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(subject.router, prefix="/subjects", tags=["subjects"])
app.include_router(topic.router, prefix="/topics", tags=["topics"])
app.include_router(question.router, prefix="/questions", tags=["questions"])
app.include_router(question_option.router, prefix="/question-options", tags=["question-options"])
app.include_router(exam.router, prefix="/exams", tags=["exams"])
app.include_router(warning.router, prefix="/warnings", tags=["warnings"])

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