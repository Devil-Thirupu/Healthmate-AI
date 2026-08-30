from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class MedicationItemSchema(BaseModel):
    drug_name: str
    normalized_name: Optional[str] = "Not available in source"
    dosage: Optional[str] = "Not available in source"
    frequency: Optional[str] = "Not available in source"
    duration: Optional[str] = "Not available in source"
    instructions: Optional[str] = "Not available in source"
    confidence: Optional[float] = None
    source_snippet: Optional[str] = None

class ExtractionCorrectionCreate(BaseModel):
    field_name: str # "drug_name", "dosage", "frequency", "duration", "instructions"
    item_index: int = 0
    original_value: Optional[str] = None
    corrected_value: str
    notes: Optional[str] = None

class ExtractionCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    extraction_id: Optional[int] = None
    document_id: int
    user_id: int
    field_name: str
    item_index: int
    original_value: Optional[str] = None
    corrected_value: str
    notes: Optional[str] = None
    created_at: datetime

class PrescriptionExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    user_id: int
    provider: str
    model_name: str
    model_version: str
    raw_output_text: Optional[str] = None
    doctor_name: Optional[str] = "Not available in source"
    clinic_name: Optional[str] = "Not available in source"
    patient_name: Optional[str] = "Not available in source"
    prescription_date: Optional[str] = "Not available in source"
    diagnosis: Optional[str] = "Not available in source"
    notes: Optional[str] = "Not available in source"
    medications_json: List[Dict[str, Any]] = []
    confidence_score: Optional[float] = None
    confidence_level: str = "NOT_AVAILABLE"
    parsing_status: str = "SUCCESS"
    is_user_reviewed: bool = False
    user_review_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UserReviewConfirmRequest(BaseModel):
    notes: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
