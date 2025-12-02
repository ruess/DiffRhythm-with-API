"""
Configuration management for DiffRhythm API
"""
import os
from pathlib import Path
from typing import List


class Settings:
    """Application settings"""
    
    # API Server
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "*"
    ).split(",")
    
    # Storage
    BASE_DIR: Path = Path(__file__).parent.parent
    STORAGE_PATH: Path = BASE_DIR / "api_storage"
    
    # Task settings
    MAX_TASK_AGE_SECONDS: int = 86400  # 24 hours
    
    # DiffRhythm settings
    DIFFRHYTHM_BASE_DIR: Path = BASE_DIR
    
    def __init__(self):
        """Initialize settings and create necessary directories"""
        self.STORAGE_PATH.mkdir(exist_ok=True)


settings = Settings()
