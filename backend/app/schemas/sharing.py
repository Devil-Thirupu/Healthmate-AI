from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SharedLinkCreate(BaseModel):
    title: Optional[str] = "Medical Records Access"
    recipient_name: Optional[str] = None
    document_ids: List[int] = []
    is_pin_protected: Optional[bool] = False
    pin: Optional[str] = None # 4-6 digit numeric pin if enabled
    duration_hours: Optional[int] = 24 # Default 24 hours expiry
    max_access_count: Optional[int] = 10
    allow_download: Optional[bool] = False
    allow_ai_summary: Optional[bool] = True

class SharedLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    title: str
    recipient_name: Optional[str] = None
    document_ids_json: List[int] = []
    is_pin_protected: bool
    expires_at: datetime
    max_access_count: int
    access_count: int
    is_active: bool
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
    allow_download: bool
    allow_ai_summary: bool
    patient_name: str
    documents: List[Dict[str, Any]] = []
    health_summary: Optional[Dict[str, Any]] = None
