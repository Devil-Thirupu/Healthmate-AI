from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# Prescription Schemas
class PrescriptionBase(BaseModel):
    medication_name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = "Tablet"
    route: Optional[str] = "Oral"
    frequency: Optional[str] = None
    timing_instructions: Optional[str] = None
    duration: Optional[str] = None
    quantity: Optional[str] = None
    refill_count: Optional[int] = 0
    doctor_name: Optional[str] = None
    prescribed_date: Optional[str] = None
    diagnosis_context: Optional[str] = None
    instructions_tamil: Optional[str] = None
    instructions_tanglish: Optional[str] = None

class PrescriptionCreate(PrescriptionBase):
    document_id: Optional[int] = None
    confidence_score: Optional[float] = 1.0

class PrescriptionUpdate(BaseModel):
    medication_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    timing_instructions: Optional[str] = None
    duration: Optional[str] = None
    quantity: Optional[str] = None
    instructions_tamil: Optional[str] = None
    instructions_tanglish: Optional[str] = None

class PrescriptionResponse(PrescriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: Optional[int] = None
    user_id: int
    confidence_score: float
    is_manual_edited: bool
    created_at: datetime
    updated_at: datetime


# Lab Test Schemas
class LabTestBase(BaseModel):
    test_name: str
    canonical_name: Optional[str] = None
    test_category: Optional[str] = "General"
    observed_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    reference_range_text: Optional[str] = None
    flag: Optional[str] = "normal"
    test_date: Optional[str] = None
    lab_name: Optional[str] = None
    explanation_tamil: Optional[str] = None
    explanation_tanglish: Optional[str] = None

class LabTestCreate(LabTestBase):
    document_id: Optional[int] = None
    confidence_score: Optional[float] = 1.0

class LabTestUpdate(BaseModel):
    test_name: Optional[str] = None
    observed_value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    reference_range_text: Optional[str] = None
    flag: Optional[str] = None
    test_date: Optional[str] = None
    explanation_tamil: Optional[str] = None
    explanation_tanglish: Optional[str] = None

class LabTestResponse(LabTestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: Optional[int] = None
    user_id: int
    confidence_score: float
    is_manual_edited: bool
    created_at: datetime
    updated_at: datetime


# Vital Record Schemas
class VitalRecordBase(BaseModel):
    record_date: str
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    blood_glucose_fasting: Optional[float] = None
    blood_glucose_postprandial: Optional[float] = None
    hba1c: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    oxygen_saturation_spo2: Optional[float] = None
    temperature_c: Optional[float] = None
    notes: Optional[str] = None

class VitalRecordCreate(VitalRecordBase):
    pass

class VitalRecordResponse(VitalRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
