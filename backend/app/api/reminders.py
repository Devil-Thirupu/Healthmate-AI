from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, timezone

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.reminder import MedicationReminder, ReminderStatus
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.reminder_service import reminder_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.reminder import (
    MedicationReminderOut, MedicationReminderCreate, MedicationReminderUpdate,
    SnoozeReminderRequest, MedicationScheduleOut, DailyHealthInsightsOut,
    ReportInsightCardOut
)

router = APIRouter()

@router.get("/today", response_model=List[MedicationReminderOut])
def get_today_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns today's medication reminders strictly for the authenticated patient."""
    return reminder_service.get_today_reminders(db=db, user_id=current_user.id)

@router.get("/upcoming", response_model=List[MedicationReminderOut])
def get_upcoming_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns all active upcoming medication reminders for the patient."""
    return reminder_service.get_today_reminders(db=db, user_id=current_user.id)

@router.get("/schedule", response_model=MedicationScheduleOut)
def get_medication_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns the categorized medication schedule (Morning, Afternoon, Night)."""
    return reminder_service.get_medication_schedule(db=db, user_id=current_user.id)

@router.post("/sync", response_model=List[MedicationReminderOut])
def sync_reminders(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Synchronizes reminders from user's extracted prescription records."""
    reminders = reminder_service.sync_reminders_from_prescriptions(db=db, user_id=current_user.id)
    if request:
        audit_service.log_event(
            db=db,
            action="MEDICATION_REMINDER_SYNC",
            resource_type="medication_reminder",
            user_id=current_user.id,
            resource_id=f"count_{len(reminders)}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"synced_count": len(reminders)}
        )
    return reminder_service.get_today_reminders(db=db, user_id=current_user.id)

@router.post("/create", response_model=MedicationReminderOut)
def create_reminder(
    reminder_in: MedicationReminderCreate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Creates a new user-configured medication reminder linked to prescription."""
    reminder = MedicationReminder(
        user_id=current_user.id,
        prescription_id=reminder_in.prescription_id,
        document_id=reminder_in.document_id,
        medicine_name=reminder_in.medicine_name,
        dosage=reminder_in.dosage,
        frequency=reminder_in.frequency,
        timing=reminder_in.timing or "Timing not specified in the available prescription.",
        scheduled_time=reminder_in.scheduled_time,
        start_date=reminder_in.start_date,
        end_date=reminder_in.end_date,
        page_number=reminder_in.page_number,
        status=ReminderStatus.PENDING.value,
        enabled=reminder_in.enabled,
        created_at=datetime.now(timezone.utc)
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    if request:
        audit_service.log_event(
            db=db,
            action="MEDICATION_REMINDER_CREATED",
            resource_type="medication_reminder",
            user_id=current_user.id,
            resource_id=str(reminder.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"medicine_name": reminder.medicine_name, "timing": reminder.timing}
        )

    return reminder

@router.post("/{reminder_id}/complete", response_model=MedicationReminderOut)
def complete_reminder(
    reminder_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Marks a medication reminder as completed."""
    reminder = reminder_service.complete_reminder(db=db, user_id=current_user.id, reminder_id=reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication reminder not found or not owned by user."
        )

    if request:
        audit_service.log_event(
            db=db,
            action="MEDICATION_REMINDER_COMPLETED",
            resource_type="medication_reminder",
            user_id=current_user.id,
            resource_id=str(reminder.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"medicine_name": reminder.medicine_name, "status": reminder.status}
        )

    return reminder

@router.post("/{reminder_id}/snooze", response_model=MedicationReminderOut)
def snooze_reminder(
    reminder_id: int,
    snooze_req: SnoozeReminderRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Snoozes a medication reminder for specified minutes."""
    reminder = reminder_service.snooze_reminder(
        db=db,
        user_id=current_user.id,
        reminder_id=reminder_id,
        minutes=snooze_req.snooze_minutes
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication reminder not found or not owned by user."
        )

    if request:
        audit_service.log_event(
            db=db,
            action="MEDICATION_REMINDER_SNOOZED",
            resource_type="medication_reminder",
            user_id=current_user.id,
            resource_id=str(reminder.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"snooze_minutes": snooze_req.snooze_minutes}
        )

    return reminder

@router.put("/{reminder_id}", response_model=MedicationReminderOut)
def update_reminder(
    reminder_id: int,
    update_data: MedicationReminderUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Updates medication reminder parameters (e.g. scheduled time, enabled flag)."""
    reminder = reminder_service.update_reminder(
        db=db,
        user_id=current_user.id,
        reminder_id=reminder_id,
        scheduled_time=update_data.scheduled_time,
        enabled=update_data.enabled,
        status=update_data.status
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication reminder not found or not owned by user."
        )

    if request:
        audit_service.log_event(
            db=db,
            action="MEDICATION_REMINDER_UPDATED",
            resource_type="medication_reminder",
            user_id=current_user.id,
            resource_id=str(reminder.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"enabled": reminder.enabled, "scheduled_time": reminder.scheduled_time}
        )

    return reminder

@router.get("/daily-insights", response_model=DailyHealthInsightsOut)
def get_daily_health_insights(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns today's aggregated health insights (medications, latest biomarkers, USDA daily food ideas)."""
    insights = reminder_service.get_daily_health_insights(db=db, user_id=current_user.id)
    if request:
        audit_service.log_event(
            db=db,
            action="NUTRITION_VIEWED",
            resource_type="daily_health_insights",
            user_id=current_user.id,
            resource_id="daily_dashboard",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"date": insights["date"]}
        )
    return insights

@router.get("/report-insights/{document_id}", response_model=ReportInsightCardOut)
def get_report_insight_card(
    document_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns report intelligence insights card for an uploaded document."""
    card = reminder_service.get_report_insight_card(db=db, user_id=current_user.id, document_id=document_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not owned by user."
        )

    if request:
        audit_service.log_event(
            db=db,
            action="REPORT_INSIGHT_GENERATED",
            resource_type="report_insight",
            user_id=current_user.id,
            resource_id=str(document_id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"total_extracted": card["total_measurements_extracted"]}
        )

    return card
