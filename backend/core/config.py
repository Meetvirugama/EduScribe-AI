import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # Storage
    UPLOAD_DIR: str = "storage/uploads"
    OUTPUT_DIR: str = "storage/outputs"
    TEMP_DIR: str = "storage/temp"
    TRANSCRIPT_DIR: str = "storage/transcripts"
    EMBEDDING_DIR: str = "storage/embeddings"
    
    # AI Models
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    
    # Upload Limits
    MAX_VIDEO_SIZE_MB: int = 1024
    SUPPORTED_VIDEO_FORMATS: str = "mp4,mkv,mov,avi"
    SUPPORTED_AUDIO_FORMATS: str = "mp3,wav,m4a"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
