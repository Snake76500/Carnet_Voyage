import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Carnet de Voyage"
    PROJECT_DESCRIPTION: str = "Carnet de voyage personnel interactif avec carte et timeline façon Polarsteps"
    VERSION: str = "1.0.0"
    
    # Database config: defaults to SQLite for immediate local dev, or PostgreSQL when configured via env
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./travel_journal.db"
    )
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "travel-journal-super-secret-key-change-in-production")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
