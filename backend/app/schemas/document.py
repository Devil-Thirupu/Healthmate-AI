from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    title: str
    category: Optional[str] = "other"
    document_date: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_or_lab: Optional[str] = None
    specialty: Optional[str] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    document_date: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_or_lab: Optional[str] = None
    specialty: Optional[str] = None
    is_archived: Optional[bool] = None

class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    file_size_bytes: int
    mime_type: str
    file_hash_sha256: str
    ocr_status: str
    ocr_confidence_score: float
    ocr_language_detected: Optional[str] = "en"
    has_manual_corrections: bool
    is_archived: bool
    metadata_json: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class DocumentDetailResponse(DocumentResponse):
    ocr_raw_text: Optional[str] = None
    prescriptions: List[Dict[str, Any]] = []
    lab_tests: List[Dict[str, Any]] = []

class DocumentCorrectionRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    document_date: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_or_lab: Optional[str] = None
    ocr_raw_text: Optional[str] = None
    prescriptions: Optional[List[Dict[str, Any]]] = None
    lab_tests: Optional[List[Dict[str, Any]]] = None
