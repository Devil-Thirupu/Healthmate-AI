from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash
from backend.app.core.config import settings as _cfg
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.clinical import Prescription, LabTest, VitalRecord
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.models.sharing import SharedLink
from backend.app.schemas.sharing import (
    SharedLinkCreate, SharedLinkResponse, SharedLinkAccessRequest, SharedLinkPublicView
)
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.audit_service import audit_service
from backend.app.services.storage_service import storage_service
from backend.app.core.logging import logger

router = APIRouter()

@router.post("/create", response_model=SharedLinkResponse, status_code=status.HTTP_201_CREATED)
def create_shared_link(
    share_in: SharedLinkCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a time-limited, patient-controlled sharing link with explicit record authorization."""
    # 1. Validate documents
    valid_doc_ids = []
    if share_in.document_ids:
        user_docs = db.query(Document.id).filter(
            Document.id.in_(share_in.document_ids),
            Document.user_id == current_user.id
        ).all()
        valid_doc_ids = [d[0] for d in user_docs]

    # 2. Validate lab tests
    valid_lab_ids = []
    if share_in.lab_ids:
        user_labs = db.query(LabTest.id).filter(
            LabTest.id.in_(share_in.lab_ids),
            LabTest.user_id == current_user.id
        ).all()
        valid_lab_ids = [l[0] for l in user_labs]

    # 3. Validate prescriptions
    valid_rx_ids = []
    if share_in.prescription_ids:
        user_rxs = db.query(Prescription.id).filter(
            Prescription.id.in_(share_in.prescription_ids),
            Prescription.user_id == current_user.id
        ).all()
        valid_rx_ids = [r[0] for r in user_rxs]

    # 4. Validate vitals
    valid_vital_ids = []
    if share_in.vital_ids:
        user_vitals = db.query(VitalRecord.id).filter(
            VitalRecord.id.in_(share_in.vital_ids),
            VitalRecord.user_id == current_user.id
        ).all()
        valid_vital_ids = [v[0] for v in user_vitals]

    # 5. Validate appointment summaries
    valid_summary_ids = []
    if share_in.appointment_summary_ids:
        user_sums = db.query(AppointmentSummary.id).filter(
            AppointmentSummary.id.in_(share_in.appointment_summary_ids),
            AppointmentSummary.user_id == current_user.id
        ).all()
        valid_summary_ids = [s[0] for s in user_sums]

    # If no specific resource list was supplied at all (backward-compat), default to user's active documents
    if not (valid_doc_ids or valid_lab_ids or valid_rx_ids or valid_vital_ids or valid_summary_ids):
        all_docs = db.query(Document.id).filter(
            Document.user_id == current_user.id,
            Document.is_archived == False
        ).all()
        valid_doc_ids = [d[0] for d in all_docs]

    duration = share_in.duration_hours if share_in.duration_hours and share_in.duration_hours > 0 else 24
    expires_at = datetime.now(timezone.utc) + timedelta(hours=duration)
    
    pin_hash = None
    if share_in.is_pin_protected and share_in.pin:
        pin_hash = get_password_hash(share_in.pin.strip())

    shared_link = SharedLink(
        user_id=current_user.id,
        title=share_in.title or "Medical Records Access",
        recipient_name=share_in.recipient_name,
        document_ids_json=valid_doc_ids,
        lab_ids_json=valid_lab_ids,
        prescription_ids_json=valid_rx_ids,
        vital_ids_json=valid_vital_ids,
        appointment_summary_ids_json=valid_summary_ids,
        permission=share_in.permission or "READ_ONLY",
        is_pin_protected=bool(share_in.is_pin_protected and share_in.pin),
        pin_hash=pin_hash,
        expires_at=expires_at,
        max_access_count=share_in.max_access_count or 20,
        access_count=0,
        is_active=True,
        allow_download=bool(share_in.allow_download),
        allow_ai_summary=bool(share_in.allow_ai_summary)
    )
    db.add(shared_link)
    db.commit()
    db.refresh(shared_link)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="RECORD_SHARED",
        resource_type="shared_link",
        user_id=current_user.id,
        resource_id=str(shared_link.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={
            "recipient": share_in.recipient_name,
            "doc_count": len(valid_doc_ids),
            "lab_count": len(valid_lab_ids),
            "rx_count": len(valid_rx_ids),
            "vital_count": len(valid_vital_ids),
            "summary_count": len(valid_summary_ids),
            "expires_at": expires_at.isoformat()
        }
    )

    resp = SharedLinkResponse.model_validate(shared_link)
    resp.share_url = f"/shared/{shared_link.token}"
    return resp

@router.get("/my-links", response_model=List[SharedLinkResponse])
@router.get("", response_model=List[SharedLinkResponse])
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
        resp.share_url = f"/shared/{link.token}"
        result.append(resp)
    return result

@router.get("/{link_id}", response_model=SharedLinkResponse)
def get_shared_link_by_id(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve owner details for a specific share link."""
    link = db.query(SharedLink).filter(
        SharedLink.id == link_id,
        SharedLink.user_id == current_user.id
    ).first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")

    resp = SharedLinkResponse.model_validate(link)
    resp.share_url = f"/shared/{link.token}"
    return resp

@router.post("/{link_id}/revoke")
@router.delete("/{link_id}")
def revoke_shared_link(
    link_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Instantly revokes an active sharing link."""
    link = db.query(SharedLink).filter(
        SharedLink.id == link_id,
        SharedLink.user_id == current_user.id
    ).first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found")

    link.is_active = False
    link.revoked_at = datetime.now(timezone.utc)
    db.commit()

    audit_service.log_event(
        db=db,
        action="SHARE_REVOKED",
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
            "permission": "READ_ONLY",
            "message": "This medical record share link has expired, was revoked, or reached its maximum view limit."
        }

    user = db.query(User).filter(User.id == link.user_id).first()
    return {
        "title": link.title,
        "recipient_name": link.recipient_name,
        "is_valid": True,
        "is_pin_required": link.is_pin_protected,
        "permission": link.permission or "READ_ONLY",
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
    """Access strictly authorized records with PIN verification."""
    link = db.query(SharedLink).filter(SharedLink.token == token).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid share link")

    now = datetime.now(timezone.utc)
    expires_at = link.expires_at.replace(tzinfo=timezone.utc) if link.expires_at.tzinfo is None else link.expires_at
    if not link.is_active or now > expires_at or link.access_count >= link.max_access_count:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This share link has expired, was revoked, or reached maximum allowable views"
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

    # Log successful share view
    audit_service.log_event(
        db=db,
        action="SHARED_RECORD_VIEWED",
        resource_type="shared_link",
        user_id=link.user_id,
        resource_id=str(link.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"recipient": link.recipient_name, "access_count": link.access_count}
    )

    user = db.query(User).filter(User.id == link.user_id).first()
    
    # 1. Fetch authorized documents
    doc_ids = link.document_ids_json or []
    documents = db.query(Document).filter(
        Document.id.in_(doc_ids),
        Document.user_id == link.user_id
    ).all() if doc_ids else []

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
                    "duration": p.duration
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

    # 2. Fetch authorized lab tests (if shared independently)
    lab_ids = link.lab_ids_json or []
    standalone_labs = db.query(LabTest).filter(
        LabTest.id.in_(lab_ids),
        LabTest.user_id == link.user_id
    ).all() if lab_ids else []

    # 3. Fetch authorized prescriptions
    rx_ids = link.prescription_ids_json or []
    standalone_rxs = db.query(Prescription).filter(
        Prescription.id.in_(rx_ids),
        Prescription.user_id == link.user_id
    ).all() if rx_ids else []

    # 4. Fetch authorized vitals
    vital_ids = link.vital_ids_json or []
    standalone_vitals = db.query(VitalRecord).filter(
        VitalRecord.id.in_(vital_ids),
        VitalRecord.user_id == link.user_id
    ).all() if vital_ids else []

    # 5. Fetch authorized appointment summaries
    sum_ids = link.appointment_summary_ids_json or []
    standalone_sums = db.query(AppointmentSummary).filter(
        AppointmentSummary.id.in_(sum_ids),
        AppointmentSummary.user_id == link.user_id
    ).all() if sum_ids else []

    return {
        "title": link.title,
        "recipient_name": link.recipient_name,
        "patient_name": user.full_name if user else "Patient",
        "permission": link.permission or "READ_ONLY",
        "expires_at": link.expires_at,
        "allow_download": link.allow_download,
        "allow_ai_summary": link.allow_ai_summary,
        "documents": docs_data,
        "lab_tests": [
            {
                "test_name": l.test_name,
                "observed_value": l.observed_value,
                "unit": l.unit,
                "flag": l.flag,
                "reference_range": l.reference_range_text,
                "date": l.test_date
            }
            for l in standalone_labs
        ],
        "prescriptions": [
            {
                "medication_name": p.medication_name,
                "dosage": p.dosage,
                "frequency": p.frequency,
                "timing": p.timing_instructions,
                "date": p.prescribed_date
            }
            for p in standalone_rxs
        ],
        "vitals": [
            {
                "date": v.record_date,
                "bp": f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}" if v.blood_pressure_systolic else "N/A",
                "heart_rate": v.heart_rate
            }
            for v in standalone_vitals
        ],
        "appointment_summaries": [
            {
                "id": s.id,
                "title": s.title,
                "summary_data": s.summary_data
            }
            for s in standalone_sums
        ]
    }

@router.get("/public/{token}/document/{doc_id}/preview")
def preview_shared_document(
    token: str,
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Serve authorized document inline for public share viewer.
    Validates token validity, expiration, revocation, and document ID authorization.
    """
    link = db.query(SharedLink).filter(SharedLink.token == token).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid share link")

    now = datetime.now(timezone.utc)
    expires_at = link.expires_at.replace(tzinfo=timezone.utc) if link.expires_at.tzinfo is None else link.expires_at
    if not link.is_active or now > expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This share link has expired or was revoked")

    # Verify that this doc_id was explicitly shared
    doc_ids = link.document_ids_json or []
    if doc_id not in doc_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document not authorized in this share link")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == link.user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Supabase Storage path: issue a signed URL redirect
    supabase_path = (doc.metadata_json or {}).get("supabase_storage_path", "")
    if supabase_path and _cfg.supabase_enabled:
        try:
            from backend.app.services.supabase_storage_service import supabase_storage
            signed_url = supabase_storage.create_signed_url(
                storage_path=supabase_path,
                category=doc.category,
                expiry_seconds=3600,
            )
            if signed_url:
                return RedirectResponse(url=signed_url, status_code=302)
        except Exception as exc:
            logger.warning(f"[Supabase] Preview signed URL failed in share view, falling back to local: {exc}")

    # Fallback local disk
    safe_path = storage_service.resolve_safe_path(link.user_id, doc.stored_filename)
    if not safe_path or not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing on server")

    return FileResponse(
        path=safe_path,
        media_type=doc.mime_type,
        content_disposition_type="inline"
    )

@router.get("/public/{token}/document/{doc_id}/download")
def download_shared_document(
    token: str,
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Download authorized document for public share viewer if allow_download is permitted.
    """
    link = db.query(SharedLink).filter(SharedLink.token == token).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid share link")

    now = datetime.now(timezone.utc)
    expires_at = link.expires_at.replace(tzinfo=timezone.utc) if link.expires_at.tzinfo is None else link.expires_at
    if not link.is_active or now > expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This share link has expired or was revoked")

    if not link.allow_download:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document download is not permitted by patient")

    doc_ids = link.document_ids_json or []
    if doc_id not in doc_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document not authorized in this share link")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == link.user_id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    audit_service.log_event(
        db=db,
        action="SHARED_DOC_DOWNLOADED",
        resource_type="shared_link",
        user_id=link.user_id,
        resource_id=f"share_{link.id}_doc_{doc.id}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    supabase_path = (doc.metadata_json or {}).get("supabase_storage_path", "")
    if supabase_path and _cfg.supabase_enabled:
        try:
            from backend.app.services.supabase_storage_service import supabase_storage
            signed_url = supabase_storage.create_signed_url(
                storage_path=supabase_path,
                category=doc.category,
                expiry_seconds=3600,
            )
            if signed_url:
                return RedirectResponse(url=signed_url, status_code=302)
        except Exception as exc:
            logger.warning(f"[Supabase] Download signed URL failed in share view, falling back to local: {exc}")

    safe_path = storage_service.resolve_safe_path(link.user_id, doc.stored_filename)
    if not safe_path or not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing on server")

    return FileResponse(
        path=safe_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )
