from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditLog
from backend.app.core.logging import logger

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        resource_type: str,
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditLog]:
        """Record an audit trail entry for compliance and security monitoring."""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id is not None else None,
                ip_address=ip_address,
                user_agent=user_agent[:250] if user_agent else None,
                details_json=details or {}
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        except Exception as e:
            logger.error(f"Failed to record audit event '{action}': {e}")
            db.rollback()
    @staticmethod
    def log(
        db: Session,
        action: str,
        resource_type: str = "general",
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Optional[AuditLog]:
        """Convenience alias for log_event."""
        return AuditService.log_event(
            db=db,
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

audit_service = AuditService()
