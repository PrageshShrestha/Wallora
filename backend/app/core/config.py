from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Wallora"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database - Local PostgreSQL
    DB_USER: str = os.getenv("DB_USER", "wallora")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "wallora123")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "wallora")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "wallora-secret-key-2024")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Upload Directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR.parent / "uploads"
    ORIGINALS_DIR: Path = UPLOAD_DIR / "originals"
    THUMBNAILS_DIR: Path = UPLOAD_DIR / "thumbnails"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create directories
for dir_path in [settings.UPLOAD_DIR, settings.ORIGINALS_DIR, settings.THUMBNAILS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)