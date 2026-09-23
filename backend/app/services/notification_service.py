from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.app.models.reminder import Notification, NotificationType, MedicationReminder, ReminderStatus
from backend.app.models.user import User

class NotificationService:
    """
    HealthMate AI Notification Engine (Phase 13)
    Manages in-app notifications for:
      - Medication Reminders
      - Report Insights
      - Appointment Reminders
      - General Health Reminders
    Enforces strict user isolation.
    """

    def create_notification(
        self,
        db: Session,
        user_id: int,
        type: str,
        title: str,
        message: str,
        related_resource_type: Optional[str] = None,
        related_resource_id: Optional[str] = None
    ) -> Notification:
        """Creates a new in-app notification for user."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_resource_type=related_resource_type,
            related_resource_id=related_resource_id,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Fetches notifications and summary counts for user with user isolation."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

        # Count today's and upcoming reminders
        today_reminders_count = db.query(MedicationReminder).filter(
            MedicationReminder.user_id == user_id,
            MedicationReminder.enabled == True,
            MedicationReminder.status != ReminderStatus.COMPLETED.value
        ).count()

        upcoming_reminders_count = db.query(MedicationReminder).filter(
            MedicationReminder.user_id == user_id,
            MedicationReminder.enabled == True
        ).count()

        return {
            "unread_count": unread_count,
            "notifications": notifications,
            "today_reminders_count": today_reminders_count,
            "upcoming_reminders_count": upcoming_reminders_count
        }

    def mark_as_read(self, db: Session, user_id: int, notification_id: int) -> Optional[Notification]:
        """Marks a single notification as read if owned by user."""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)
        return notification

    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        """Marks all notifications as read for user."""
        updated = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        db.commit()
        return updated

notification_service = NotificationService()
