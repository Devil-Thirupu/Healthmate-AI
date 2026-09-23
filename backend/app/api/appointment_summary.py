from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Any
import io

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.appointment_summary_service import appointment_summary_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.appointment_summary import (
    AppointmentSummaryGenerateRequest,
    AppointmentSummaryUpdateRequest,
    AppointmentSummaryResponse,
    AppointmentSummaryListItem
)

router = APIRouter()

@router.post("/generate", response_model=AppointmentSummaryResponse, status_code=status.HTTP_201_CREATED)
def generate_appointment_summary(
    req: AppointmentSummaryGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generates a structured Appointment Preparation & Health Summary from verified user records.
    Applies Evidence Guard zero-hallucination policies and health trend calculation.
    """
    summary = appointment_summary_service.generate_summary(
        db=db,
        user_id=current_user.id,
        req=req
    )

    audit_service.log_event(
        db=db,
        action="APPOINTMENT_SUMMARY_GENERATE",
        resource_type="appointment_summary",
        user_id=current_user.id,
        resource_id=str(summary.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"title": summary.title}
    )

    return summary

@router.get("/list", response_model=List[AppointmentSummaryListItem])
def list_appointment_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Lists all appointment preparation summaries created by the authenticated user."""
    return db.query(AppointmentSummary).filter(
        AppointmentSummary.user_id == current_user.id
    ).order_by(AppointmentSummary.created_at.desc()).all()

@router.get("/{summary_id}", response_model=AppointmentSummaryResponse)
def get_appointment_summary(
    summary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieves a specific appointment summary with user isolation enforcement."""
    summary = db.query(AppointmentSummary).filter(
        AppointmentSummary.id == summary_id,
        AppointmentSummary.user_id == current_user.id
    ).first()

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment summary not found or unauthorized access"
        )

    return summary

@router.put("/{summary_id}", response_model=AppointmentSummaryResponse)
def update_appointment_summary(
    summary_id: int,
    update_req: AppointmentSummaryUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Updates user review modifications (questions, section exclusions, custom notes).
    Does NOT alter raw medical records in the database.
    """
    summary = appointment_summary_service.update_summary(
        db=db,
        user_id=current_user.id,
        summary_id=summary_id,
        update_req=update_req
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment summary not found or unauthorized access"
        )

    audit_service.log_event(
        db=db,
        action="APPOINTMENT_SUMMARY_UPDATE",
        resource_type="appointment_summary",
        user_id=current_user.id,
        resource_id=str(summary.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"updated_title": summary.title}
    )

    return summary

@router.get("/{summary_id}/pdf")
def download_appointment_summary_pdf(
    summary_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Renders and streams the publication-grade Appointment Preparation PDF.
    Strictly verifies user ownership before generating document.
    """
    summary = db.query(AppointmentSummary).filter(
        AppointmentSummary.id == summary_id,
        AppointmentSummary.user_id == current_user.id
    ).first()

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment summary not found or unauthorized access"
        )

    pdf_buffer = appointment_summary_service.generate_pdf(summary=summary, user=current_user)

    audit_service.log_event(
        db=db,
        action="APPOINTMENT_SUMMARY_PDF_EXPORT",
        resource_type="appointment_summary",
        user_id=current_user.id,
        resource_id=str(summary.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    filename = f"HealthMate_Appointment_Summary_{summary.id}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )
