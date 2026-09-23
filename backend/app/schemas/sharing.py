from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SharedLinkCreate(BaseModel):
    title: Optional[str] = "Medical Records Access"
    recipient_name: Optional[str] = None
    document_ids: Optional[List[int]] = []
    lab_ids: Optional[List[int]] = []
    prescription_ids: Optional[List[int]] = []
    vital_ids: Optional[List[int]] = []
    appointment_summary_ids: Optional[List[int]] = []
    permission: Optional[str] = "READ_ONLY"
    is_pin_protected: Optional[bool] = False
    pin: Optional[str] = None # 4-6 digit numeric pin if enabled
    duration_hours: Optional[int] = 24 # Default 24 hours expiry (supports 1, 6, 24, 72, 168, etc.)
    max_access_count: Optional[int] = 20
    allow_download: Optional[bool] = False
    allow_ai_summary: Optional[bool] = True

class SharedLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    title: str
    recipient_name: Optional[str] = None
    document_ids_json: List[int] = []
    lab_ids_json: List[int] = []
    prescription_ids_json: List[int] = []
    vital_ids_json: List[int] = []
    appointment_summary_ids_json: List[int] = []
    permission: str = "READ_ONLY"
    is_pin_protected: bool
    expires_at: datetime
    max_access_count: int
    access_count: int
    is_active: bool
    revoked_at: Optional[datetime] = None
    allow_download: bool
    allow_ai_summary: bool
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    share_url: Optional[str] = None

class SharedLinkAccessRequest(BaseModel):
    pin: Optional[str] = None

class SharedLinkPublicView(BaseModel):
    title: str
    recipient_name: Optional[str] = None
    is_pin_required: bool
    is_valid: bool
    expires_at: datetime
    permission: str = "READ_ONLY"
    allow_download: bool
    allow_ai_summary: bool
    patient_name: str
    documents: List[Dict[str, Any]] = []
    lab_tests: List[Dict[str, Any]] = []
    prescriptions: List[Dict[str, Any]] = []
    vitals: List[Dict[str, Any]] = []
    appointment_summaries: List[Dict[str, Any]] = []
    health_summary: Optional[Dict[str, Any]] = None
