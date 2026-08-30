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

@router.get("/", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve audit history for user actions and security events."""
    query = db.query(AuditLog)
    
    # If not admin, restrict strictly to current user's logs
    if current_user.role != UserRole.ADMIN.value:
        query = query.filter(AuditLog.user_id == current_user.id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
        
    return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
