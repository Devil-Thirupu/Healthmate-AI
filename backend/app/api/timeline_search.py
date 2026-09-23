from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.health_timeline_service import health_timeline_service
from backend.app.services.global_search_service import global_search_service
from backend.app.services.health_intelligence_service import health_intelligence_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.timeline_search import (
    TimelineResponse, GlobalSearchResponse, DoctorVisitSummaryResponse,
    ExplainReportRequest, ExplainReportResponse
)

router = APIRouter()

@router.get("/health-timeline", response_model=TimelineResponse, tags=["Health Timeline"])
def get_health_timeline(
    category: str = Query("ALL", description="Filter: ALL, REPORTS, LAB_TESTS, PRESCRIPTIONS, VITALS, APPOINTMENTS"),
    date_range: str = Query("all", description="Filter: 30d, 3m, 6m, 1y, all"),
    q: Optional[str] = Query(None, description="Optional search term"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns the comprehensive multi-source chronological medical history timeline for the authenticated patient:
    - Combines Reports, Lab Tests, Prescriptions, Vitals, and Appointments
    - Evaluates previous record comparisons for lab tests
    - Strictly isolated to the authenticated user
    """
    timeline_data = health_timeline_service.get_health_timeline(
        db=db,
        user_id=current_user.id,
        category=category,
        date_range=date_range,
        search_query=q
    )

    if request:
        audit_service.log_event(
            db=db,
            action="TIMELINE_VIEWED",
            resource_type="health_timeline",
            user_id=current_user.id,
            resource_id=f"events_{timeline_data['filtered_events_count']}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"category": category, "date_range": date_range, "query": q}
        )

    return timeline_data

@router.get("/health-search", response_model=GlobalSearchResponse, tags=["Global Health Search"])
def search_health_records(
    q: str = Query(..., min_length=1, description="Unified search query for health records"),
    limit: int = Query(30, ge=1, le=100),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Unified Hybrid Global Search Engine across:
    - Structured exact matches: Test names, values, medication names, prescription details, document dates
    - Semantic matches: Document OCR chunks with Evidence Guard
    - Enforces strict user isolation
    """
    search_data = global_search_service.search_health_records(
        db=db,
        user_id=current_user.id,
        query=q,
        limit=limit
    )

    if request:
        audit_service.log_event(
            db=db,
            action="GLOBAL_SEARCH_PERFORMED",
            resource_type="global_search",
            user_id=current_user.id,
            resource_id=f"results_{search_data['total_results']}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"query_len": len(q), "total_found": search_data["total_results"]}
        )

    return search_data

@router.get("/doctor-visit", response_model=DoctorVisitSummaryResponse, tags=["Doctor Visit Mode"])
def get_doctor_visit_summary(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns clinical briefing summary for doctor consultations:
    - Recent reports and extracted findings
    - Current prescription medications
    - Multi-point biomarker trend lines
    - Out-of-range flagged measurements
    - Doctor discussion questions
    - Source document traceability
    """
    summary = health_intelligence_service.get_doctor_visit_summary(
        db=db,
        user_id=current_user.id
    )

    if request:
        audit_service.log_event(
            db=db,
            action="DOCTOR_VISIT_MODE_ACCESSED",
            resource_type="doctor_visit_summary",
            user_id=current_user.id,
            resource_id="doctor_visit_mode",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"reports_count": len(summary["recent_reports"])}
        )

    return summary

@router.post("/reports/{document_id}/explain", response_model=ExplainReportResponse, tags=["Report Intelligence"])
def explain_uploaded_report(
    document_id: int,
    explain_req: ExplainReportRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generates grounded "Explain My Report" response (Phase 14):
    - REPORT OVERVIEW
    - YOUR RECORDED VALUES
    - WHAT CHANGED
    - WHAT THE TEST GENERALLY MEASURES
    - IMPORTANT
    - SOURCES
    Supports English, Tamil, and Tanglish.
    """
    target_lang = explain_req.language or current_user.language_preference or "en"
    explanation = health_intelligence_service.explain_report(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
        language=target_lang
    )

    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not owned by the authenticated user."
        )

    if request:
        audit_service.log_event(
            db=db,
            action="REPORT_EXPLAINED",
            resource_type="report_explanation",
            user_id=current_user.id,
            resource_id=str(document_id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"document_id": document_id, "language": target_lang}
        )

    return explanation
