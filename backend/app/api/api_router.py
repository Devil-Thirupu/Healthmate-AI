from fastapi import APIRouter
from backend.app.api.auth import router as auth_router
from backend.app.api.documents import router as documents_router
from backend.app.api.audit import router as audit_router
from backend.app.api.sharing import router as sharing_router
from backend.app.api.health_intelligence import router as health_intelligence_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(sharing_router, prefix="/sharing", tags=["Patient Sharing"])
api_router.include_router(audit_router, prefix="/audit", tags=["Audit & Compliance"])
api_router.include_router(health_intelligence_router, prefix="/health-intelligence", tags=["Health Intelligence"])
