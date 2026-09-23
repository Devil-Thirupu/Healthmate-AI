from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any, Dict

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.notification_service import notification_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.reminder import NotificationOut, NotificationSummaryOut

router = APIRouter()

@router.get("", response_model=NotificationSummaryOut)
def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns in-app notifications and unread summary for the authenticated user."""
    summary = notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )

    if request:
        audit_service.log_event(
            db=db,
            action="NOTIFICATION_VIEWED",
            resource_type="notification",
            user_id=current_user.id,
            resource_id=f"count_{len(summary['notifications'])}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"unread_count": summary["unread_count"]}
        )

    return summary

@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Marks a single notification as read."""
    notification = notification_service.mark_as_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or not owned by user."
        )

    return notification

@router.post("/read-all", response_model=Dict[str, int])
def mark_all_notifications_read(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Marks all user notifications as read."""
    marked = notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    return {"marked_read_count": marked}
