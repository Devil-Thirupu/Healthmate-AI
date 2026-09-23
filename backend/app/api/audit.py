from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.audit import AuditLog
from backend.app.schemas.audit import AuditLogResponse
from backend.app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[AuditLogResponse])
@router.get("/", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    category: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve audit history for user actions and security events with category filtering."""
    query = db.query(AuditLog)
    
    # Strict user isolation: Non-admin can only see their own audit logs
    if current_user.role != UserRole.ADMIN.value:
        query = query.filter(AuditLog.user_id == current_user.id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if category:
        cat_lower = category.strip().lower()
        if cat_lower == "login":
            query = query.filter(AuditLog.action.in_([
                "AUTH_LOGIN_SUCCESS", "AUTH_LOGIN_FAILED", "AUTH_GOOGLE_SUCCESS", "AUTH_GOOGLE_FAILED", "USER_REGISTER", "AUTH_PASSWORD_CHANGE"
            ]))
        elif cat_lower == "documents":
            query = query.filter(
                (AuditLog.resource_type == "document") | 
                (AuditLog.action.ilike("DOCUMENT_%"))
            )
        elif cat_lower == "ai":
            query = query.filter(
                (AuditLog.action.ilike("%AI%")) |
                (AuditLog.action.ilike("%ASSISTANT%")) |
                (AuditLog.action.ilike("%EXPLAIN%"))
            )
        elif cat_lower == "sharing":
            query = query.filter(
                (AuditLog.resource_type == "shared_link") |
                (AuditLog.action.in_(["RECORD_SHARED", "SHARE_REVOKED", "SHARED_RECORD_VIEWED", "SHARE_CREATE", "SHARE_REVOKE", "SHARE_ACCESS_SUCCESS"]))
            )
        
    return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
