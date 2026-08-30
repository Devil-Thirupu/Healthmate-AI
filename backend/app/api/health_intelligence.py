from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.health_intelligence_service import health_intelligence_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.health_intelligence import (
    HealthIntelligenceSummary, BiomarkerTrendSeries, ReportComparisonMatrix,
    CompareReportsRequest, TimelineEvent
)

router = APIRouter()

@router.get("/summary", response_model=HealthIntelligenceSummary)
def get_health_intelligence_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns the comprehensive Health Intelligence overview:
    - Tracked biomarkers count
    - Recent changes between historical lab reports
    - Percentage changes, trend directions, and reference range statuses
    - Source document traceability
    """
    return health_intelligence_service.get_user_health_intelligence_summary(
        db=db,
        user_id=current_user.id
    )

@router.get("/trends", response_model=List[BiomarkerTrendSeries])
def get_biomarker_trends(
    test_name: Optional[str] = Query(None, description="Optional canonical or display test name filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns time-series data points formatted for Recharts line charts.
    Enforces unit safety: never combines incompatible units into the same series.
    """
    return health_intelligence_service.get_biomarker_trends(
        db=db,
        user_id=current_user.id,
        canonical_name=test_name
    )

@router.post("/compare-reports", response_model=ReportComparisonMatrix)
def compare_selected_reports(
    compare_req: CompareReportsRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Cross-tabulates and compares biomarkers across 2 or more selected medical reports.
    Enforces user authorization and prevents cross-user document leakage.
    """
    if len(compare_req.document_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 document IDs are required for comparison."
        )

    # Verify that all requested documents belong to the current user
    user_docs = db.query(Document).filter(
        Document.id.in_(compare_req.document_ids),
        Document.user_id == current_user.id
    ).all()

    if len(user_docs) != len(set(compare_req.document_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more selected documents do not exist or do not belong to the authenticated user."
        )

    matrix = health_intelligence_service.compare_selected_reports(
        db=db,
        user_id=current_user.id,
        document_ids=compare_req.document_ids
    )

    if request:
        audit_service.log_event(
            db=db,
            action="HEALTH_INTELLIGENCE_REPORT_COMPARISON",
            resource_type="report_comparison",
            user_id=current_user.id,
            resource_id=f"docs:{','.join(map(str, compare_req.document_ids))}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"document_ids": compare_req.document_ids, "tests_compared": matrix["total_tests_compared"]}
        )

    return matrix

@router.get("/timeline", response_model=List[TimelineEvent])
def get_chronological_health_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns the complete chronological health history timeline for the patient:
    - Grouped by document date
    - Lists extracted lab measurements and prescriptions for each event
    """
    return health_intelligence_service.get_chronological_timeline(
        db=db,
        user_id=current_user.id
    )
