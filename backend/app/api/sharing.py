from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.clinical import Prescription, LabTest
from backend.app.models.sharing import SharedLink
from backend.app.schemas.sharing import (
    SharedLinkCreate, SharedLinkResponse, SharedLinkAccessRequest, SharedLinkPublicView
)
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.audit_service import audit_service
from backend.app.core.logging import logger

router = APIRouter()

@router.post("/create", response_model=SharedLinkResponse, status_code=status.HTTP_201_CREATED)
def create_shared_link(
    share_in: SharedLinkCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a time-limited, patient-controlled sharing link with optional PIN."""
    # Verify documents belong to current user
    if share_in.document_ids:
        user_docs = db.query(Document.id).filter(
            Document.id.in_(share_in.document_ids),
            Document.user_id == current_user.id
        ).all()
        valid_ids = [d[0] for d in user_docs]
    else:
        # Share all active documents of this user
        all_docs = db.query(Document.id).filter(
            Document.user_id == current_user.id,
            Document.is_archived == False
        ).all()
        valid_ids = [d[0] for d in all_docs]

    expires_at = datetime.now(timezone.utc) + timedelta(hours=share_in.duration_hours or 24)
    
    pin_hash = None
    if share_in.is_pin_protected and share_in.pin:
        pin_hash = get_password_hash(share_in.pin.strip())

    shared_link = SharedLink(
        user_id=current_user.id,
        title=share_in.title or "Medical Records Access",
        recipient_name=share_in.recipient_name,
        document_ids_json=valid_ids,
        is_pin_protected=bool(share_in.is_pin_protected and share_in.pin),
        pin_hash=pin_hash,
        expires_at=expires_at,
        max_access_count=share_in.max_access_count or 10,
        access_count=0,
        is_active=True,
        allow_download=bool(share_in.allow_download),
        allow_ai_summary=bool(share_in.allow_ai_summary)
    )
    db.add(shared_link)
    db.commit()
    db.refresh(shared_link)

    # Log audit trail
    audit_service.log_event(
        db=db,
        action="SHARE_CREATE",
        resource_type="shared_link",
        user_id=current_user.id,
        resource_id=str(shared_link.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={
            "recipient": share_in.recipient_name,
            "doc_count": len(valid_ids),
            "pin_protected": shared_link.is_pin_protected,
            "expires_at": expires_at.isoformat()
        }
    )

    resp = SharedLinkResponse.model_validate(shared_link)
    resp.share_url = f"/share/{shared_link.token}"
    return resp

@router.get("/my-links", response_model=List[SharedLinkResponse])
def list_my_shared_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all active and past sharing links created by the current patient."""
    links = db.query(SharedLink).filter(
        SharedLink.user_id == current_user.id
    ).order_by(desc(SharedLink.created_at)).all()

    result = []
    for link in links:
        resp = SharedLinkResponse.model_validate(link)
        resp.share_url = f"/share/{link.token}"
        result.append(resp)
    return result

@router.delete("/{link_id}")
def revoke_shared_link(
    link_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Instantly revoke an active sharing link."""
    link = db.query(SharedLink).filter(
        SharedLink.id == link_id,
        SharedLink.user_id == current_user.id
    ).first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")

    link.is_active = False
    db.commit()

    audit_service.log_event(
        db=db,
        action="SHARE_REVOKE",
        resource_type="shared_link",
        user_id=current_user.id,
        resource_id=str(link.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    return {"status": "success", "message": "Shared link has been revoked"}

@router.get("/public/{token}")
def get_shared_records_metadata(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Public check endpoint for a shared link: returns basic info and whether PIN is required."""
    link = db.query(SharedLink).filter(SharedLink.token == token).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired share link")

    now = datetime.now(timezone.utc)
    expires_at = link.expires_at.replace(tzinfo=timezone.utc) if link.expires_at.tzinfo is None else link.expires_at
    if not link.is_active or now > expires_at or link.access_count >= link.max_access_count:
        return {
            "title": link.title,
            "recipient_name": link.recipient_name,
            "is_valid": False,
            "is_pin_required": link.is_pin_protected,
            "message": "This medical record share link has expired or reached its maximum view limit."
        }

    user = db.query(User).filter(User.id == link.user_id).first()
    return {
        "title": link.title,
        "recipient_name": link.recipient_name,
        "is_valid": True,
        "is_pin_required": link.is_pin_protected,
        "patient_name": user.full_name if user else "Patient",
        "expires_at": link.expires_at,
        "allow_download": link.allow_download,
        "allow_ai_summary": link.allow_ai_summary
    }

@router.post("/public/{token}/access")
def access_shared_records(
    token: str,
    payload: SharedLinkAccessRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Access shared records with PIN verification."""
    link = db.query(SharedLink).filter(SharedLink.token == token).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid share link")

    now = datetime.now(timezone.utc)
    expires_at = link.expires_at.replace(tzinfo=timezone.utc) if link.expires_at.tzinfo is None else link.expires_at
    if not link.is_active or now > expires_at or link.access_count >= link.max_access_count:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This share link has expired or reached maximum allowable views"
        )

    # Check PIN if protected
    if link.is_pin_protected:
        if not payload.pin or not link.pin_hash or not verify_password(payload.pin.strip(), link.pin_hash):
            audit_service.log_event(
                db=db,
                action="SHARE_ACCESS_PIN_FAILED",
                resource_type="shared_link",
                user_id=link.user_id,
                resource_id=str(link.id),
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("User-Agent")
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect access PIN")

    # Increment access count
    link.access_count += 1
    link.last_accessed_at = datetime.now(timezone.utc)
    db.commit()

    # Log successful share access
    audit_service.log_event(
        db=db,
        action="SHARE_ACCESS_SUCCESS",
        resource_type="shared_link",
        user_id=link.user_id,
        resource_id=str(link.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"recipient": link.recipient_name, "access_count": link.access_count}
    )

    # Fetch authorized documents and extracted medical records
    user = db.query(User).filter(User.id == link.user_id).first()
    doc_ids = link.document_ids_json or []
    documents = db.query(Document).filter(
        Document.id.in_(doc_ids),
        Document.user_id == link.user_id
    ).all()

    docs_data = []
    for doc in documents:
        prescriptions = db.query(Prescription).filter(Prescription.document_id == doc.id).all()
        lab_tests = db.query(LabTest).filter(LabTest.document_id == doc.id).all()
        docs_data.append({
            "id": doc.id,
            "title": doc.title,
            "category": doc.category,
            "document_date": doc.document_date,
            "doctor_name": doc.doctor_name,
            "clinic_or_lab": doc.clinic_or_lab,
            "mime_type": doc.mime_type,
            "ocr_status": doc.ocr_status,
            "prescriptions": [
                {
                    "medication_name": p.medication_name,
                    "dosage": p.dosage,
                    "frequency": p.frequency,
                    "timing_instructions": p.timing_instructions,
                    "duration": p.duration,
                    "instructions_tamil": p.instructions_tamil,
                    "instructions_tanglish": p.instructions_tanglish
                }
                for p in prescriptions
            ],
            "lab_tests": [
                {
                    "test_name": l.test_name,
                    "observed_value": l.observed_value,
                    "unit": l.unit,
                    "reference_range_text": l.reference_range_text,
                    "flag": l.flag,
                    "test_date": l.test_date
                }
                for l in lab_tests
            ]
        })

    return {
        "title": link.title,
        "recipient_name": link.recipient_name,
        "patient_name": user.full_name if user else "Patient",
        "patient_dob": user.date_of_birth if user else None,
        "patient_gender": user.gender if user else None,
        "patient_blood_group": user.blood_group if user else None,
        "patient_allergies": user.allergies if user else None,
        "patient_chronic_conditions": user.chronic_conditions if user else None,
        "expires_at": link.expires_at,
        "allow_download": link.allow_download,
        "allow_ai_summary": link.allow_ai_summary,
        "documents": docs_data
    }
