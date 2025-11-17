from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.db import create_db_and_tables
from src.routers import user, subject,topics
from src.models import __all__

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    await create_db_and_tables()
    yield

app = FastAPI(
    title="Education Platform API",
    description="Backend API for Education Platform with Keycloak Auth",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
#app.include_router(product.router, prefix="/api/products", tags=["products"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(subject.router, prefix="/api/subject",tags=["subject"])
app.include_router(topics.router, prefix="/api/topics", tags=["topics"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Education Platform API is running"}