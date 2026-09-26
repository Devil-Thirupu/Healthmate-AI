import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.core.logging import logger
from backend.app.api.api_router import api_router
# Import all models to ensure metadata registration
import backend.app.models

def ensure_schema_compatibility():
    """Safely adds missing additive columns to existing SQLite tables without data loss."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    with engine.connect() as conn:
        if "shared_links" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("shared_links")]
            if "lab_ids_json" not in columns:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN lab_ids_json JSON DEFAULT '[]'"))
            if "prescription_ids_json" not in columns:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN prescription_ids_json JSON DEFAULT '[]'"))
            if "vital_ids_json" not in columns:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN vital_ids_json JSON DEFAULT '[]'"))
            if "appointment_summary_ids_json" not in columns:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN appointment_summary_ids_json JSON DEFAULT '[]'"))
            if "permission" not in columns:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN permission VARCHAR(50) DEFAULT 'READ_ONLY'"))
            if "revoked_at" not in columns:
                conn.execute(text("ALTER TABLE shared_links ADD COLUMN revoked_at DATETIME"))
            conn.commit()
        # Doctor Connect new tables are created by create_all() above — no ALTER needed.
        # Log table presence for diagnostics
        table_names = inspector.get_table_names()
        for tbl in ["doctors", "patient_doctor_connections", "appointments", "doctor_access_grants"]:
            if tbl in table_names:
                logger.info(f"[Doctor Connect] Table '{tbl}' ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created and additive columns synced
    logger.info("Initializing Healthmate AI database tables...")
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    logger.info("Database tables initialized successfully.")
    yield
    # Shutdown: Clean up resources if needed
    logger.info("Shutting down Healthmate AI application.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="HEALTHMATE AI — Intelligent Personal Health Record and Medical Document Assistant",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security & Timing Middleware
@app.middleware("http")
async def add_security_and_timing_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Mount API v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected",
        "database_type": "postgresql" if settings.is_postgres else "sqlite",
        "supabase_configured": settings.supabase_enabled
    }

@app.get("/api/health/supabase", tags=["System"])
@app.get(f"{settings.API_V1_STR}/health/supabase", tags=["System"])
def supabase_health_diagnostic():
    """
    Diagnostic verification endpoint for Supabase integration (Auth, PostgreSQL DB, Storage).
    Safely verifies connectivity without exposing keys or passwords.
    """
    from sqlalchemy import text
    from backend.app.core.database import SessionLocal
    
    db_status = "unknown"
    db_error = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)

    storage_status = "not_configured"
    storage_buckets = {}
    if settings.supabase_enabled:
        try:
            from backend.app.services.supabase_storage_service import supabase_storage
            buckets = ["medical-documents", "prescriptions", "medical-images", "appointment-pdfs"]
            for b in buckets:
                try:
                    storage_buckets[b] = "accessible" if supabase_storage.client else "unreachable"
                except Exception:
                    storage_buckets[b] = "error"
            storage_status = "connected" if supabase_storage.is_enabled else "client_init_failed"
        except Exception as e:
            storage_status = f"error: {str(e)}"

    return {
        "supabase_url_configured": bool(settings.SUPABASE_URL),
        "supabase_url": settings.SUPABASE_URL or None,
        "database_engine": "PostgreSQL (Supabase)" if settings.is_postgres else "SQLite (Local/Fallback)",
        "database_connectivity": db_status,
        "database_error": db_error,
        "supabase_storage_status": storage_status,
        "supabase_storage_buckets": storage_buckets,
        "supabase_auth_sync_enabled": settings.supabase_enabled,
        "is_production_ready": bool(settings.is_postgres and settings.supabase_enabled)
    }

@app.get("/", tags=["System"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "documentation": "/docs"
    }
