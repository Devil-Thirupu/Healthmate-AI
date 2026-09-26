"""Pydantic schemas for Doctor Connect — HealthMate AI"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# ---------------------------------------------------------------------------
# Doctor schemas
# ---------------------------------------------------------------------------

class DoctorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    specialization: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    consultation_type: Optional[str] = "in_person"
    available_days: Optional[str] = None
    available_time: Optional[str] = None
    notes: Optional[str] = None


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    consultation_type: Optional[str] = None
    available_days: Optional[str] = None
    available_time: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialization: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    consultation_type: Optional[str] = None
    available_days: Optional[str] = None
    available_time: Optional[str] = None
    profile_image_url: Optional[str] = None
    verification_status: str
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Connection status from the patient's perspective (injected at query time)
    connection_status: Optional[str] = None
    connection_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Connection schemas
# ---------------------------------------------------------------------------

class ConnectionRequest(BaseModel):
    doctor_id: int
    patient_note: Optional[str] = None


class ConnectionUpdate(BaseModel):
    status: str  # accepted | rejected | cancelled | disconnected
    doctor_note: Optional[str] = None


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    status: str
    patient_note: Optional[str] = None
    doctor_note: Optional[str] = None
    requested_at: datetime
    responded_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    created_at: datetime
    doctor: Optional[DoctorResponse] = None


# ---------------------------------------------------------------------------
# Appointment schemas
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    doctor_id: int
    requested_date: str = Field(..., description="ISO date YYYY-MM-DD")
    requested_time: Optional[str] = None
    consultation_type: Optional[str] = "in_person"
    reason: Optional[str] = None
    patient_note: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Patient can cancel; doctor-side updates are future work."""
    status: Optional[str] = None          # cancelled by patient
    reason: Optional[str] = None
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    patient_note: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    connection_id: Optional[int] = None
    requested_date: str
    requested_time: Optional[str] = None
    consultation_type: Optional[str] = None
    reason: Optional[str] = None
    patient_note: Optional[str] = None
    status: str
    doctor_note: Optional[str] = None
    confirmed_date: Optional[str] = None
    confirmed_time: Optional[str] = None
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime
    doctor: Optional[DoctorResponse] = None


# ---------------------------------------------------------------------------
# Doctor Access Grant schemas
# ---------------------------------------------------------------------------

class AccessGrantCreate(BaseModel):
    doctor_id: int
    # Granular permissions (all default False — patient must opt in)
    share_blood_type: bool = False
    share_age: bool = False
    share_current_medications: bool = False
    share_prescriptions: bool = False
    share_lab_reports: bool = False
    share_vital_records: bool = False
    share_medical_documents: bool = False
    share_health_timeline: bool = False
    share_ai_health_summary: bool = False
    share_appointment_summaries: bool = False
    # Specific IDs (empty list = share all records in the allowed category)
    document_ids: Optional[List[int]] = []
    lab_ids: Optional[List[int]] = []
    prescription_ids: Optional[List[int]] = []
    vital_ids: Optional[List[int]] = []
    # Access control
    allow_download: bool = False
    duration_hours: int = Field(default=168, ge=1, le=8760)  # Default 7 days, max 1 year


class AccessGrantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grant_token: str
    patient_id: int
    doctor_id: int
    connection_id: Optional[int] = None
    share_blood_type: bool
    share_age: bool
    share_current_medications: bool
    share_prescriptions: bool
    share_lab_reports: bool
    share_vital_records: bool
    share_medical_documents: bool
    share_health_timeline: bool
    share_ai_health_summary: bool
    share_appointment_summaries: bool
    allow_download: bool
    expires_at: datetime
    is_active: bool
    revoked_at: Optional[datetime] = None
    access_count: int
    last_accessed_at: Optional[datetime] = None
    created_at: datetime
    doctor: Optional[DoctorResponse] = None
    # Derived public URL (injected at response time)
    grant_url: Optional[str] = None


class AccessGrantPublicView(BaseModel):
    """What an authorized doctor sees when they open the grant link."""
    is_valid: bool
    is_expired: bool
    is_revoked: bool
    expires_at: datetime
    allow_download: bool
    # Patient summary (only fields the patient authorised)
    patient_name: str                                    # always shown
    patient_blood_type: Optional[str] = None
    patient_age: Optional[str] = None
    current_medications: List[Dict[str, Any]] = []
    prescriptions: List[Dict[str, Any]] = []
    lab_reports: List[Dict[str, Any]] = []
    vital_records: List[Dict[str, Any]] = []
    medical_documents: List[Dict[str, Any]] = []
    appointment_summaries: List[Dict[str, Any]] = []
    # Source / metadata
    record_count: int = 0
    accessed_at: Optional[datetime] = None
