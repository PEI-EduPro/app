import logging
import sys
from src.core.settings import settings
from pydantic_settings import BaseSettings, SettingsConfigDict

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger("sqlalchemy.engine").setLevel(getattr(logging, settings.SQLALCHEMY_LOG_LEVEL.upper()))
    logging.getLogger("uvicorn").setLevel(getattr(logging, settings.UVICORN_LOG_LEVEL.upper()))