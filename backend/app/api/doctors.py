"""
Doctor Connect API — HealthMate AI
===================================
Endpoints:
  /doctors                       — CRUD for doctor profiles
  /doctors/connections           — Patient ↔ Doctor connection management
  /doctors/appointments          — Appointment requests
  /doctors/access-grants         — Granular medical record sharing authorizations
  /doctors/access-grants/view/{token} — Public doctor-facing record viewer
"""

from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.models.user import User
from backend.app.models.doctor import (
    Doctor, PatientDoctorConnection, Appointment, DoctorAccessGrant,
    ConnectionStatus, AppointmentStatus
)
from backend.app.models.clinical import Prescription, LabTest, VitalRecord
from backend.app.models.document import Document
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.models.reminder import Notification, NotificationType
from backend.app.schemas.doctor import (
    DoctorCreate, DoctorUpdate, DoctorResponse,
    ConnectionRequest, ConnectionUpdate, ConnectionResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AccessGrantCreate, AccessGrantResponse, AccessGrantPublicView,
)
from backend.app.services.audit_service import audit_service
from backend.app.core.logging import logger

router = APIRouter()


# ===========================================================================
# SECTION 1 — DOCTOR MANAGEMENT
# ===========================================================================

@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a doctor profile")
def create_doctor(
    doctor_in: DoctorCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new doctor profile associated with the current patient."""
    doctor = Doctor(
        name=doctor_in.name,
        specialization=doctor_in.specialization,
        hospital_or_clinic=doctor_in.hospital_or_clinic,
        phone_number=doctor_in.phone_number,
        email=doctor_in.email,
        address=doctor_in.address,
        consultation_type=doctor_in.consultation_type,
        available_days=doctor_in.available_days,
        available_time=doctor_in.available_time,
        notes=doctor_in.notes,
        created_by_user_id=current_user.id,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    audit_service.log(
        db=db, user_id=current_user.id,
        action="DOCTOR_CREATED",
        resource_type="doctor",
        resource_id=str(doctor.id),
        ip_address=get_client_ip(request),
        details={"doctor_name": doctor.name}
    )
    resp = DoctorResponse.model_validate(doctor)
    return resp


@router.get("/", response_model=List[DoctorResponse], summary="List all doctors for current patient")
def list_doctors(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all doctor profiles created by or connected to the current patient."""
    # Doctors created by this patient (own records)
    query = db.query(Doctor).filter(Doctor.created_by_user_id == current_user.id)
    if not include_inactive:
        query = query.filter(Doctor.is_active == True)
    doctors = query.order_by(desc(Doctor.created_at)).all()

    result = []
    for doc in doctors:
        resp = DoctorResponse.model_validate(doc)
        # Annotate with connection status
        conn = (
            db.query(PatientDoctorConnection)
            .filter(
                PatientDoctorConnection.patient_id == current_user.id,
                PatientDoctorConnection.doctor_id == doc.id
            )
            .order_by(desc(PatientDoctorConnection.created_at))
            .first()
        )
        if conn:
            resp.connection_status = conn.status
            resp.connection_id = conn.id
        result.append(resp)
    return result


@router.get("/{doctor_id}", response_model=DoctorResponse, summary="Get a doctor profile")
def get_doctor(
    doctor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    doctor = _get_doctor_for_patient(doctor_id, current_user.id, db)
    resp = DoctorResponse.model_validate(doctor)
    conn = (
        db.query(PatientDoctorConnection)
        .filter(
            PatientDoctorConnection.patient_id == current_user.id,
            PatientDoctorConnection.doctor_id == doctor_id
        )
        .order_by(desc(PatientDoctorConnection.created_at))
        .first()
    )
    if conn:
        resp.connection_status = conn.status
        resp.connection_id = conn.id
    return resp


@router.put("/{doctor_id}", response_model=DoctorResponse, summary="Update a doctor profile")
def update_doctor(
    doctor_id: int,
    doctor_in: DoctorUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    doctor = _get_doctor_for_patient(doctor_id, current_user.id, db)
    for field, value in doctor_in.model_dump(exclude_none=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    audit_service.log(
        db=db, user_id=current_user.id,
        action="DOCTOR_UPDATED",
        resource_type="doctor",
        resource_id=str(doctor.id),
        ip_address=get_client_ip(request),
        details={"updated_fields": list(doctor_in.model_dump(exclude_none=True).keys())}
    )
    return DoctorResponse.model_validate(doctor)


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Soft-delete (deactivate) a doctor profile")
def deactivate_doctor(
    doctor_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    doctor = _get_doctor_for_patient(doctor_id, current_user.id, db)
    doctor.is_active = False
    db.commit()
    audit_service.log(
        db=db, user_id=current_user.id,
        action="DOCTOR_DEACTIVATED",
        resource_type="doctor",
        resource_id=str(doctor.id),
        ip_address=get_client_ip(request),
        details={"doctor_name": doctor.name}
    )


# ===========================================================================
# SECTION 2 — CONNECTIONS
# ===========================================================================

@router.post("/connections/request", response_model=ConnectionResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Request a connection with a doctor")
def request_connection(
    conn_in: ConnectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    doctor = _get_doctor_for_patient(conn_in.doctor_id, current_user.id, db)

    # Prevent duplicate active connections
    existing = (
        db.query(PatientDoctorConnection)
        .filter(
            PatientDoctorConnection.patient_id == current_user.id,
            PatientDoctorConnection.doctor_id == conn_in.doctor_id,
            PatientDoctorConnection.status.in_([
                ConnectionStatus.PENDING.value, ConnectionStatus.ACCEPTED.value
            ])
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A {existing.status} connection with this doctor already exists (ID: {existing.id})"
        )

    conn = PatientDoctorConnection(
        patient_id=current_user.id,
        doctor_id=conn_in.doctor_id,
        patient_note=conn_in.patient_note,
        status=ConnectionStatus.PENDING.value,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)

    # Notification for patient
    _create_notification(
        db=db, user_id=current_user.id,
        title="Connection Request Sent",
        message=f"Your connection request to Dr. {doctor.name} has been sent.",
        resource_type="patient_doctor_connection",
        resource_id=str(conn.id)
    )

    audit_service.log(
        db=db, user_id=current_user.id,
        action="DOCTOR_CONNECTED",
        resource_type="patient_doctor_connection",
        resource_id=str(conn.id),
        ip_address=get_client_ip(request),
        details={"doctor_id": conn_in.doctor_id, "status": "pending"}
    )

    resp = ConnectionResponse.model_validate(conn)
    resp.doctor = DoctorResponse.model_validate(doctor)
    return resp


@router.get("/connections", response_model=List[ConnectionResponse],
            summary="List all doctor connections for current patient")
def list_connections(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    query = (
        db.query(PatientDoctorConnection)
        .options(joinedload(PatientDoctorConnection.doctor))
        .filter(PatientDoctorConnection.patient_id == current_user.id)
    )
    if status_filter:
        query = query.filter(PatientDoctorConnection.status == status_filter)
    connections = query.order_by(desc(PatientDoctorConnection.created_at)).all()

    result = []
    for c in connections:
        resp = ConnectionResponse.model_validate(c)
        if c.doctor:
            resp.doctor = DoctorResponse.model_validate(c.doctor)
        result.append(resp)
    return result


@router.patch("/connections/{connection_id}", response_model=ConnectionResponse,
              summary="Update connection status (cancel/disconnect)")
def update_connection(
    connection_id: int,
    update_in: ConnectionUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    conn = _get_connection(connection_id, current_user.id, db)

    allowed_transitions = {
        ConnectionStatus.PENDING.value: [ConnectionStatus.CANCELLED.value],
        ConnectionStatus.ACCEPTED.value: [ConnectionStatus.DISCONNECTED.value],
    }
    allowed = allowed_transitions.get(conn.status, [])
    if update_in.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot transition from '{conn.status}' to '{update_in.status}'"
        )

    conn.status = update_in.status
    if update_in.status == ConnectionStatus.DISCONNECTED.value:
        conn.disconnected_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conn)

    audit_service.log(
        db=db, user_id=current_user.id,
        action="DOCTOR_DISCONNECTED" if update_in.status == "disconnected" else "CONNECTION_UPDATED",
        resource_type="patient_doctor_connection",
        resource_id=str(conn.id),
        ip_address=get_client_ip(request),
        details={"new_status": update_in.status}
    )

    resp = ConnectionResponse.model_validate(conn)
    if conn.doctor:
        resp.doctor = DoctorResponse.model_validate(conn.doctor)
    return resp


# ===========================================================================
# SECTION 3 — APPOINTMENTS
# ===========================================================================

@router.post("/appointments", response_model=AppointmentResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Request an appointment with a connected doctor")
def request_appointment(
    appt_in: AppointmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    IMPORTANT: Status is set to 'pending'. The appointment is NOT confirmed until
    the doctor explicitly accepts it.
    """
    doctor = _get_doctor_for_patient(appt_in.doctor_id, current_user.id, db)

    # Check there is an accepted connection (optional soft check — warn but do not block)
    accepted_conn = (
        db.query(PatientDoctorConnection)
        .filter(
            PatientDoctorConnection.patient_id == current_user.id,
            PatientDoctorConnection.doctor_id == appt_in.doctor_id,
            PatientDoctorConnection.status == ConnectionStatus.ACCEPTED.value
        )
        .first()
    )

    appt = Appointment(
        patient_id=current_user.id,
        doctor_id=appt_in.doctor_id,
        connection_id=accepted_conn.id if accepted_conn else None,
        requested_date=appt_in.requested_date,
        requested_time=appt_in.requested_time,
        consultation_type=appt_in.consultation_type,
        reason=appt_in.reason,
        patient_note=appt_in.patient_note,
        status=AppointmentStatus.PENDING.value,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # Notification
    _create_notification(
        db=db, user_id=current_user.id,
        title="Appointment Request Sent",
        message=f"Your appointment request to Dr. {doctor.name} for {appt_in.requested_date} has been submitted and is awaiting confirmation.",
        resource_type="appointment",
        resource_id=str(appt.id)
    )

    audit_service.log(
        db=db, user_id=current_user.id,
        action="APPOINTMENT_REQUESTED",
        resource_type="appointment",
        resource_id=str(appt.id),
        ip_address=get_client_ip(request),
        details={
            "doctor_id": appt_in.doctor_id,
            "requested_date": appt_in.requested_date,
            "status": "pending"
        }
    )

    resp = AppointmentResponse.model_validate(appt)
    resp.doctor = DoctorResponse.model_validate(doctor)
    return resp


@router.get("/appointments", response_model=List[AppointmentResponse],
            summary="List all appointments for current patient")
def list_appointments(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    query = (
        db.query(Appointment)
        .options(joinedload(Appointment.doctor))
        .filter(Appointment.patient_id == current_user.id)
    )
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    appointments = query.order_by(desc(Appointment.created_at)).all()

    result = []
    for a in appointments:
        resp = AppointmentResponse.model_validate(a)
        if a.doctor:
            resp.doctor = DoctorResponse.model_validate(a.doctor)
        result.append(resp)
    return result


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse,
            summary="Get a specific appointment")
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    appt = _get_appointment(appointment_id, current_user.id, db)
    resp = AppointmentResponse.model_validate(appt)
    if appt.doctor:
        resp.doctor = DoctorResponse.model_validate(appt.doctor)
    return resp


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse,
              summary="Cancel an appointment (patient side)")
def update_appointment(
    appointment_id: int,
    update_in: AppointmentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    appt = _get_appointment(appointment_id, current_user.id, db)

    # Patient may only cancel; doctor-side acceptance is future work
    if update_in.status and update_in.status not in [AppointmentStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Patients may only cancel appointments via this endpoint."
        )

    for field, value in update_in.model_dump(exclude_none=True).items():
        setattr(appt, field, value)
    db.commit()
    db.refresh(appt)

    if update_in.status == AppointmentStatus.CANCELLED.value:
        audit_service.log(
            db=db, user_id=current_user.id,
            action="APPOINTMENT_CANCELLED",
            resource_type="appointment",
            resource_id=str(appt.id),
            ip_address=get_client_ip(request),
            details={"doctor_id": appt.doctor_id}
        )
        _create_notification(
            db=db, user_id=current_user.id,
            title="Appointment Cancelled",
            message=f"Your appointment request for {appt.requested_date} has been cancelled.",
            resource_type="appointment",
            resource_id=str(appt.id)
        )

    resp = AppointmentResponse.model_validate(appt)
    if appt.doctor:
        resp.doctor = DoctorResponse.model_validate(appt.doctor)
    return resp


# ===========================================================================
# SECTION 4 — DOCTOR ACCESS GRANTS (Granular Sharing)
# ===========================================================================

@router.post("/access-grants", response_model=AccessGrantResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Create a granular medical-record access grant for a doctor")
def create_access_grant(
    grant_in: AccessGrantCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Patient explicitly selects which record categories to share.
    Creates a secure, time-limited, revocable grant token.
    Medical records are PRIVATE by default; no category is shared unless explicitly enabled.
    """
    doctor = _get_doctor_for_patient(grant_in.doctor_id, current_user.id, db)

    # Verify there is an accepted connection to this doctor
    conn = (
        db.query(PatientDoctorConnection)
        .filter(
            PatientDoctorConnection.patient_id == current_user.id,
            PatientDoctorConnection.doctor_id == grant_in.doctor_id,
            PatientDoctorConnection.status == ConnectionStatus.ACCEPTED.value
        )
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must have an accepted connection with this doctor before granting access."
        )

    # Validate specific IDs belong to patient
    valid_doc_ids = _validate_ids(db, Document, "user_id", current_user.id, grant_in.document_ids or [])
    valid_lab_ids = _validate_ids(db, LabTest, "user_id", current_user.id, grant_in.lab_ids or [])
    valid_rx_ids = _validate_ids(db, Prescription, "user_id", current_user.id, grant_in.prescription_ids or [])
    valid_vital_ids = _validate_ids(db, VitalRecord, "user_id", current_user.id, grant_in.vital_ids or [])

    expires_at = datetime.now(timezone.utc) + timedelta(hours=grant_in.duration_hours)

    grant = DoctorAccessGrant(
        patient_id=current_user.id,
        doctor_id=grant_in.doctor_id,
        connection_id=conn.id,
        share_blood_type=grant_in.share_blood_type,
        share_age=grant_in.share_age,
        share_current_medications=grant_in.share_current_medications,
        share_prescriptions=grant_in.share_prescriptions,
        share_lab_reports=grant_in.share_lab_reports,
        share_vital_records=grant_in.share_vital_records,
        share_medical_documents=grant_in.share_medical_documents,
        share_health_timeline=grant_in.share_health_timeline,
        share_ai_health_summary=grant_in.share_ai_health_summary,
        share_appointment_summaries=grant_in.share_appointment_summaries,
        document_ids_json=valid_doc_ids,
        lab_ids_json=valid_lab_ids,
        prescription_ids_json=valid_rx_ids,
        vital_ids_json=valid_vital_ids,
        allow_download=grant_in.allow_download,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)

    audit_service.log(
        db=db, user_id=current_user.id,
        action="SHARE_CREATED",
        resource_type="doctor_access_grant",
        resource_id=str(grant.id),
        ip_address=get_client_ip(request),
        details={
            "doctor_id": grant_in.doctor_id,
            "expires_at": expires_at.isoformat(),
            "categories_shared": _shared_categories(grant_in),
        }
    )

    resp = AccessGrantResponse.model_validate(grant)
    resp.doctor = DoctorResponse.model_validate(doctor)
    resp.grant_url = f"/doctor-share/{grant.grant_token}"
    return resp


@router.get("/access-grants", response_model=List[AccessGrantResponse],
            summary="List all active access grants created by current patient")
def list_access_grants(
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    query = (
        db.query(DoctorAccessGrant)
        .options(joinedload(DoctorAccessGrant.doctor))
        .filter(DoctorAccessGrant.patient_id == current_user.id)
    )
    if active_only:
        query = query.filter(
            DoctorAccessGrant.is_active == True,
            DoctorAccessGrant.expires_at > datetime.now(timezone.utc)
        )
    grants = query.order_by(desc(DoctorAccessGrant.created_at)).all()

    result = []
    for g in grants:
        resp = AccessGrantResponse.model_validate(g)
        if g.doctor:
            resp.doctor = DoctorResponse.model_validate(g.doctor)
        resp.grant_url = f"/doctor-share/{g.grant_token}"
        result.append(resp)
    return result


@router.delete("/access-grants/{grant_id}", status_code=status.HTTP_200_OK,
               summary="Revoke an access grant immediately")
def revoke_access_grant(
    grant_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    grant = _get_grant(grant_id, current_user.id, db)
    grant.is_active = False
    grant.revoked_at = datetime.now(timezone.utc)
    db.commit()

    audit_service.log(
        db=db, user_id=current_user.id,
        action="SHARE_REVOKED",
        resource_type="doctor_access_grant",
        resource_id=str(grant.id),
        ip_address=get_client_ip(request),
        details={"doctor_id": grant.doctor_id}
    )
    return {"message": "Access grant revoked successfully.", "grant_id": grant_id}


@router.get("/access-grants/view/{grant_token}",
            response_model=AccessGrantPublicView,
            summary="Doctor-facing: view shared patient records via grant token")
def view_shared_records(
    grant_token: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Public endpoint — no authentication required (token IS the authorization).
    Called when a doctor opens the grant link.

    NEVER exposes raw DB IDs as navigation links.
    NEVER invents or infers missing patient values.
    """
    grant = db.query(DoctorAccessGrant).filter(
        DoctorAccessGrant.grant_token == grant_token
    ).first()

    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found or invalid token.")

    now = datetime.now(timezone.utc)
    expires_aware = grant.expires_at.replace(tzinfo=timezone.utc) if grant.expires_at.tzinfo is None else grant.expires_at

    is_revoked = not grant.is_active
    is_expired = expires_aware < now

    if is_revoked or is_expired:
        return AccessGrantPublicView(
            is_valid=False,
            is_expired=is_expired,
            is_revoked=is_revoked,
            expires_at=grant.expires_at,
            allow_download=False,
            patient_name="Access Unavailable",
        )

    # Load patient
    patient = db.query(User).filter(User.id == grant.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found.")

    # Increment access counter
    grant.access_count += 1
    grant.last_accessed_at = now
    db.commit()

    # Build patient summary — only authorised categories
    patient_name = patient.full_name
    blood_type = patient.blood_group if grant.share_blood_type else None
    age_str = _calculate_age(patient.date_of_birth) if grant.share_age else None

    medications: List[Any] = []
    if grant.share_current_medications or grant.share_prescriptions:
        rx_query = db.query(Prescription).filter(Prescription.user_id == patient.id)
        if grant.prescription_ids_json:
            rx_query = rx_query.filter(Prescription.id.in_(grant.prescription_ids_json))
        rxs = rx_query.all()
        medications = [
            {
                "medication_name": r.medication_name,
                "dosage": r.dosage or "Not specified",
                "frequency": r.frequency or "Not specified",
                "prescribed_date": str(r.prescribed_date) if hasattr(r, "prescribed_date") else "Not provided",
            }
            for r in rxs
        ]

    lab_data: List[Any] = []
    if grant.share_lab_reports:
        lab_query = db.query(LabTest).filter(LabTest.user_id == patient.id)
        if grant.lab_ids_json:
            lab_query = lab_query.filter(LabTest.id.in_(grant.lab_ids_json))
        labs = lab_query.order_by(desc(LabTest.test_date)).limit(50).all()
        lab_data = [
            {
                "test": l.test_name,
                "value": str(l.value) if l.value is not None else "Not provided",
                "unit": l.unit or "",
                "reference_range": l.reference_range or "Not provided",
                "date": str(l.test_date) if l.test_date else "Not provided",
                "flag": l.flag or "normal",
            }
            for l in labs
        ]

    vital_data: List[Any] = []
    if grant.share_vital_records:
        vit_query = db.query(VitalRecord).filter(VitalRecord.user_id == patient.id)
        if grant.vital_ids_json:
            vit_query = vit_query.filter(VitalRecord.id.in_(grant.vital_ids_json))
        vitals = vit_query.order_by(desc(VitalRecord.recorded_at)).limit(30).all()
        vital_data = [
            {
                "type": v.vital_type,
                "value": str(v.value) if v.value is not None else "Not provided",
                "unit": v.unit or "",
                "recorded_at": str(v.recorded_at) if v.recorded_at else "Not provided",
            }
            for v in vitals
        ]

    doc_data: List[Any] = []
    if grant.share_medical_documents:
        doc_query = db.query(Document).filter(Document.user_id == patient.id)
        if grant.document_ids_json:
            doc_query = doc_query.filter(Document.id.in_(grant.document_ids_json))
        docs = doc_query.order_by(desc(Document.uploaded_at)).limit(20).all()
        doc_data = [
            {
                "report_name": d.original_filename or "Unnamed",
                "document_type": d.category or "document",
                "report_date": str(d.report_date) if hasattr(d, "report_date") and d.report_date else "Not provided",
            }
            for d in docs
        ]

    appt_data: List[Any] = []
    if grant.share_appointment_summaries:
        appt_sums = (
            db.query(AppointmentSummary)
            .filter(AppointmentSummary.user_id == patient.id)
            .order_by(desc(AppointmentSummary.created_at))
            .limit(5)
            .all()
        )
        appt_data = [
            {
                "doctor_name": a.doctor_name or "Not provided",
                "visit_date": str(a.visit_date) if hasattr(a, "visit_date") and a.visit_date else "Not provided",
                "summary": a.summary_text[:500] if hasattr(a, "summary_text") and a.summary_text else "Not provided",
            }
            for a in appt_sums
        ]

    record_count = len(medications) + len(lab_data) + len(vital_data) + len(doc_data) + len(appt_data)

    audit_service.log(
        db=db, user_id=patient.id,
        action="SHARE_VIEWED",
        resource_type="doctor_access_grant",
        resource_id=str(grant.id),
        ip_address=get_client_ip(request),
        details={
            "viewer_ip": get_client_ip(request),
            "record_count": record_count,
            "grant_token_prefix": grant_token[:8] + "...",
        }
    )

    return AccessGrantPublicView(
        is_valid=True,
        is_expired=False,
        is_revoked=False,
        expires_at=grant.expires_at,
        allow_download=grant.allow_download,
        patient_name=patient_name,
        patient_blood_type=blood_type or "Not provided",
        patient_age=age_str or "Not provided",
        current_medications=medications,
        prescriptions=medications,
        lab_reports=lab_data,
        vital_records=vital_data,
        medical_documents=doc_data,
        appointment_summaries=appt_data,
        record_count=record_count,
        accessed_at=now,
    )


# ===========================================================================
# Private helpers
# ===========================================================================

def _get_doctor_for_patient(doctor_id: int, patient_id: int, db: Session) -> Doctor:
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.created_by_user_id == patient_id
    ).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    return doctor


def _get_connection(connection_id: int, patient_id: int, db: Session) -> PatientDoctorConnection:
    conn = db.query(PatientDoctorConnection).filter(
        PatientDoctorConnection.id == connection_id,
        PatientDoctorConnection.patient_id == patient_id
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")
    return conn


def _get_appointment(appointment_id: int, patient_id: int, db: Session) -> Appointment:
    appt = db.query(Appointment).options(joinedload(Appointment.doctor)).filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == patient_id
    ).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    return appt


def _get_grant(grant_id: int, patient_id: int, db: Session) -> DoctorAccessGrant:
    grant = db.query(DoctorAccessGrant).filter(
        DoctorAccessGrant.id == grant_id,
        DoctorAccessGrant.patient_id == patient_id
    ).first()
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access grant not found.")
    return grant


def _validate_ids(db: Session, model, owner_col: str, owner_id: int, ids: List[int]) -> List[int]:
    """Return only the IDs that belong to this patient."""
    if not ids:
        return []
    col = getattr(model, owner_col)
    rows = db.query(model.id).filter(model.id.in_(ids), col == owner_id).all()
    return [r[0] for r in rows]


def _create_notification(db: Session, user_id: int, title: str, message: str,
                          resource_type: str, resource_id: str) -> None:
    notif = Notification(
        user_id=user_id,
        type=NotificationType.APPOINTMENT_REMINDER.value,
        title=title,
        message=message,
        related_resource_type=resource_type,
        related_resource_id=resource_id,
    )
    db.add(notif)
    db.commit()


def _shared_categories(grant_in: AccessGrantCreate) -> List[str]:
    cats = []
    mapping = {
        "share_blood_type": "blood_type",
        "share_age": "age",
        "share_current_medications": "current_medications",
        "share_prescriptions": "prescriptions",
        "share_lab_reports": "lab_reports",
        "share_vital_records": "vital_records",
        "share_medical_documents": "medical_documents",
        "share_health_timeline": "health_timeline",
        "share_ai_health_summary": "ai_health_summary",
        "share_appointment_summaries": "appointment_summaries",
    }
    for field, label in mapping.items():
        if getattr(grant_in, field, False):
            cats.append(label)
    return cats


def _calculate_age(date_of_birth: Optional[str]) -> Optional[str]:
    if not date_of_birth:
        return None
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return str(age)
    except Exception:
        return None
