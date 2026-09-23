from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate, PasswordChange
)
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.audit_service import audit_service
from backend.app.core.logging import logger

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new patient / user."""
    existing = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists"
        )
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email.lower().strip(),
        hashed_password=hashed_password,
        full_name=user_in.full_name.strip(),
        role=user_in.role or UserRole.PATIENT.value,
        date_of_birth=user_in.date_of_birth,
        gender=user_in.gender,
        blood_group=user_in.blood_group,
        phone_number=user_in.phone_number,
        emergency_contact=user_in.emergency_contact,
        allergies=user_in.allergies,
        chronic_conditions=user_in.chronic_conditions,
        language_preference=user_in.language_preference or "en"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT Tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Audit Log
    audit_service.log_event(
        db=db,
        action="USER_REGISTER",
        resource_type="user",
        user_id=user.id,
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"email": user.email, "role": user.role}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

import re
from backend.app.core.config import settings
from backend.app.schemas.auth import (
    UserCreate, UserLogin, MobileLogin, GoogleLoginRequest, UserResponse, TokenResponse, UserUpdate, PasswordChange
)

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    # Strip spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone.strip())
    return cleaned

@router.post("/login", response_model=TokenResponse)
def login_user(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Authenticate with email or mobile phone number and password."""
    user = None
    
    # 1. Search by email if present
    if login_data.email:
        user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    
    # 2. Search by phone number if present
    if not user and login_data.phone_number:
        clean_phone = normalize_phone(login_data.phone_number)
        user = db.query(User).filter(User.phone_number == clean_phone).first()

    # 3. Search by identifier (could be email or phone)
    if not user and login_data.identifier:
        ident = login_data.identifier.strip()
        if "@" in ident:
            user = db.query(User).filter(User.email == ident.lower()).first()
        else:
            clean_phone = normalize_phone(ident)
            user = db.query(User).filter(User.phone_number == clean_phone).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        audit_service.log_event(
            db=db,
            action="AUTH_LOGIN_FAILED",
            resource_type="user",
            user_id=user.id if user else None,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"attempted_identifier": login_data.email or login_data.phone_number or login_data.identifier}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, mobile number, or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated"
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Audit Log
    audit_service.log_event(
        db=db,
        action="AUTH_LOGIN_SUCCESS",
        resource_type="user",
        user_id=user.id,
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"email": user.email, "method": "credentials"}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login-mobile", response_model=TokenResponse)
def login_mobile(
    login_data: MobileLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Dedicated endpoint for Mobile Number + Password login."""
    clean_phone = normalize_phone(login_data.phone_number)
    user = db.query(User).filter(User.phone_number == clean_phone).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        audit_service.log_event(
            db=db,
            action="AUTH_LOGIN_FAILED",
            resource_type="user",
            user_id=user.id if user else None,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"attempted_phone": login_data.phone_number}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect mobile number or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated"
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    audit_service.log_event(
        db=db,
        action="AUTH_LOGIN_SUCCESS",
        resource_type="user",
        user_id=user.id,
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"email": user.email, "method": "mobile_password"}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", response_model=TokenResponse)
def login_with_google(
    req: GoogleLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate with Google OAuth 2.0 Identity Token.
    Returns 503 / 400 if Google OAuth credentials are not configured in environment.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_ID.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Sign-In is not configured."
        )

    # Decode and verify token
    token_str = req.id_token.strip()
    try:
        import base64
        import json
        # Parse JWT payload safely
        parts = token_str.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        
        # Base64 decode payload
        payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)

        # Validate issuer, audience, expiration
        issuer = payload.get("iss", "")
        if issuer not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid token issuer")
        
        aud = payload.get("aud", "")
        if aud != settings.GOOGLE_CLIENT_ID:
            raise ValueError("Token audience does not match configured Google Client ID")
        
        exp = payload.get("exp", 0)
        if exp < datetime.now(timezone.utc).timestamp():
            raise ValueError("Google identity token has expired")

        email = payload.get("email")
        email_verified = payload.get("email_verified", False)
        if not email or not email_verified:
            raise ValueError("Unverified or missing Google email claim")
        
        full_name = payload.get("name", "Google User")

    except Exception as e:
        audit_service.log_event(
            db=db,
            action="AUTH_GOOGLE_FAILED",
            resource_type="user",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication token validation failed: {str(e)}"
        )

    # Match or create user
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        user = User(
            email=email.lower().strip(),
            hashed_password=get_password_hash(f"GoogleOAuth_{email}_{datetime.now().timestamp()}"),
            full_name=full_name,
            role=UserRole.PATIENT.value,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated"
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    audit_service.log_event(
        db=db,
        action="AUTH_GOOGLE_SUCCESS",
        resource_type="user",
        user_id=user.id,
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"email": user.email, "google_auth": True}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_payload: dict,
    db: Session = Depends(get_db)
) -> Any:
    """Issue a new access token from a valid refresh token."""
    token = refresh_payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh_token")
    
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current authenticated user profile."""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(
    profile_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update profile and demographics."""
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    audit_service.log_event(
        db=db,
        action="USER_PROFILE_UPDATE",
        resource_type="user",
        user_id=current_user.id,
        resource_id=str(current_user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"updated_fields": list(update_data.keys())}
    )

    return current_user

@router.put("/change-password")
def change_password(
    pwd_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change account password."""
    if not verify_password(pwd_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(pwd_data.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()

    audit_service.log_event(
        db=db,
        action="AUTH_PASSWORD_CHANGE",
        resource_type="user",
        user_id=current_user.id,
        resource_id=str(current_user.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    return {"status": "success", "message": "Password updated successfully"}
