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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created
    logger.info("Initializing Healthmate AI database tables...")
    Base.metadata.create_all(bind=engine)
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
        "database": "connected"
    }

@app.get("/", tags=["System"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "documentation": "/docs"
    }
