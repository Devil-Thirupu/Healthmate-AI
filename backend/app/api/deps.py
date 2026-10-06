from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.models.user import User, UserRole
from backend.app.core.logging import logger

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to retrieve the current authenticated user from JWT Bearer token or ?token= query param."""
    token = None
    if credentials:
        token = credentials.credentials
    elif request.query_params.get("token"):
        token = request.query_params.get("token")
    elif request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    user = None

    if payload and payload.get("type") == "access":
        user_id = payload.get("sub")
        if user_id:
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
            except (ValueError, TypeError):
                # sub is a UUID or non-integer string
                if payload.get("email"):
                    user = db.query(User).filter(User.email == payload.get("email").lower().strip()).first()
    
    # If not resolved yet, attempt to decode as Supabase Auth token
    if not user:
        try:
            from jose import jwt as jose_jwt
            claims = jose_jwt.get_unverified_claims(token)
            email = claims.get("email")
            if email:
                user = db.query(User).filter(User.email == email.lower().strip()).first()
                if not user:
                    # Auto-provision user from Supabase Auth claims if not yet in local DB
                    meta = claims.get("user_metadata", {})
                    full_name = meta.get("full_name") or meta.get("name") or email.split("@")[0]
                    role = meta.get("role") or UserRole.PATIENT.value
                    from backend.app.core.security import get_password_hash
                    user = User(
                        email=email.lower().strip(),
                        hashed_password=get_password_hash(f"Supabase_{email}_{claims.get('sub', '')}"),
                        full_name=full_name,
                        role=role,
                        phone_number=meta.get("phone_number"),
                        date_of_birth=meta.get("date_of_birth"),
                        gender=meta.get("gender") or "Male",
                        blood_group=meta.get("blood_group") or "O+",
                        language_preference=meta.get("language_preference") or "en",
                        is_active=True
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    logger.info(f"Auto-provisioned local user {user.id} for Supabase email {email}")
        except Exception as sb_err:
            logger.debug(f"Could not parse token as Supabase JWT: {sb_err}")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
        
    return user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency that returns current user if token is provided, otherwise None."""
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None

def get_client_ip(request: Request) -> str:
    """Extract client IP address considering proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
