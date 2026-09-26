import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"

# Ensure runtime directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "HEALTHMATE AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security & Tokens
    SECRET_KEY: str = "healthmate-ai-super-secret-key-2026-medical-vault-secure-jwt-token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'healthmate.db'}"
    
    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    UPLOADS_DIR: Path = UPLOADS_DIR
    DATA_DIR: Path = DATA_DIR
    NUTRITION_DIR: Path = DATA_DIR / "nutrition"
    
    # Max Upload Size (50 MB)
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024
    
    # Allowed Upload File Extensions
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".dcm", ".tiff"]
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Optional LLM API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "auto"  # auto, gemini, openai, local_fallback

    # Google OAuth 2.0 (Optional / Development Mode fallback)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ------------------------------------------------------------------
    # Supabase Integration
    # SUPABASE_URL        — project URL  (https://xxxx.supabase.co)
    # SUPABASE_SECRET_KEY — service_role key (backend-only, never frontend)
    # ------------------------------------------------------------------
    SUPABASE_URL: str = ""
    SUPABASE_SECRET_KEY: str = ""

    @property
    def is_postgres(self) -> bool:
        """True when the DATABASE_URL points at PostgreSQL (Supabase or otherwise)."""
        return self.DATABASE_URL.startswith("postgresql") or self.DATABASE_URL.startswith("postgres")

    @property
    def supabase_enabled(self) -> bool:
        """True when Supabase credentials are configured in the environment."""
        return bool(self.SUPABASE_URL and self.SUPABASE_SECRET_KEY and \
               not self.SUPABASE_SECRET_KEY.startswith("PASTE"))

settings = Settings()
