from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.auth import router as auth_router
from backend.app.api.documents import router as documents_router
from backend.app.api.audit import router as audit_router
from backend.app.api.sharing import router as sharing_router, access_shared_records, get_shared_records_metadata
from backend.app.schemas.sharing import SharedLinkAccessRequest
from backend.app.api.health_intelligence import router as health_intelligence_router
from backend.app.api.assistant import router as assistant_router
from backend.app.api.appointment_summary import router as appointment_summary_router
from backend.app.api.nutrition import router as nutrition_router
from backend.app.api.reminders import router as reminders_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.timeline_search import router as timeline_search_router
from backend.app.api.doctors import router as doctors_router  # Doctor Connect (additive)

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(sharing_router, prefix="/sharing", tags=["Patient Sharing"])
api_router.include_router(audit_router, prefix="/audit", tags=["Audit & Compliance"])
api_router.include_router(health_intelligence_router, prefix="/health-intelligence", tags=["Health Intelligence"])
api_router.include_router(assistant_router, prefix="/assistant", tags=["AI Assistant & Hybrid RAG"])
api_router.include_router(appointment_summary_router, prefix="/appointment-summary", tags=["Appointment Summary & PDF"])
api_router.include_router(nutrition_router, prefix="/nutrition", tags=["Nutrition Intelligence"])
api_router.include_router(reminders_router, prefix="/reminders", tags=["Medication Reminders"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(timeline_search_router, prefix="", tags=["Timeline, Search & Doctor Visit"])
api_router.include_router(doctors_router, prefix="/doctors", tags=["Doctor Connect"])  # additive


# Direct Shared Access Endpoints (/api/v1/shared/{token})
@api_router.get("/shared/{token}", tags=["Patient Sharing"])
def direct_shared_view(token: str, db: Session = Depends(get_db)):
    return get_shared_records_metadata(token=token, db=db)

@api_router.post("/shared/{token}", tags=["Patient Sharing"])
def direct_shared_access(
    token: str,
    payload: SharedLinkAccessRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    return access_shared_records(token=token, payload=payload, request=request, db=db)

