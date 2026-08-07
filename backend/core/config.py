"""
core/config.py — Application Settings

All configuration is read from environment variables (via .env file in dev,
secrets manager / CI env in production). Never hardcode values here.
"""
# pyrefly: ignore [missing-import]
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Authentication ────────────────────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # ── URLs ──────────────────────────────────────────────────────────────────
    BASE_URL: str = "http://localhost:5001"
    FRONTEND_URL: str = "http://localhost:5173"
    # Comma-separated list of allowed CORS origins, e.g.:
    # ALLOWED_ORIGINS=https://app.eduscribe.ai,https://staging.eduscribe.ai
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ── Storage ───────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "storage/uploads"
    OUTPUT_DIR: str = "storage/outputs"
    TEMP_DIR: str = "storage/temp"
    TRANSCRIPT_DIR: str = "storage/transcripts"
    FRAMES_DIR: str = "storage/frames"
    EMBEDDING_DIR: str = "storage/embeddings"
    YOUTUBE_API_KEY: Optional[str] = None

    # ── Retention Policy ──────────────────────────────────────────────────────
    DEFAULT_RETENTION_DAYS: int = 7
    MAX_RETENTION_DAYS: int = 15

    # ── Upload Limits ─────────────────────────────────────────────────────────
    MAX_VIDEO_SIZE_MB: int = 1024
    SUPPORTED_VIDEO_FORMATS: str = "mp4,mkv,mov,avi"
    SUPPORTED_AUDIO_FORMATS: str = "mp3,wav,m4a"

    # ── AI Models ─────────────────────────────────────────────────────────────
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"

    # ── Vision Pipeline ───────────────────────────────────────────────────────
    SCENE_DETECT_THRESHOLD: float = 27.0
    SCENE_MIN_LEN_FRAMES: int = 15
    BLUR_THRESHOLD: float = 30.0
    PHASH_THRESHOLD: int = 5
    OCR_MIN_CONFIDENCE: float = 0.70
    TRANSCRIPT_MATCH_MIN_SCORE: float = 10.0

    # ── RAG Configuration ─────────────────────────────────────────────────────
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    CHUNK_STRATEGY: str = "timestamp"       # token | semantic | timestamp | topic
    MMR_LAMBDA: float = 0.7                 # relevance vs. diversity balance
    HYBRID_BM25_ALPHA: float = 0.5          # BM25 weight in hybrid search
    EMBED_MODEL_VERSION: str = "v1"         # bump to force re-embedding
    RERANK_TOP_N: int = 3                   # final results after reranking

    # ── Upload & Processing Limits ────────────────────────────────────────────
    MAX_VIDEO_DURATION_SECONDS: int = 7200  # 2 hours
    MAX_UPLOADS_PER_HOUR: int = 5           # per user (rate limiting)
    MAX_YOUTUBE_PER_HOUR: int = 10          # per user (rate limiting)

    # ── Quality Evaluation ────────────────────────────────────────────────────
    MIN_QUALITY_SCORE: float = 0.5          # below this triggers a warning log

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return ALLOWED_ORIGINS as a parsed list for CORSMiddleware."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
