from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class BiomarkerChange(BaseModel):
    test_name: str
    canonical_name: Optional[str] = None
    test_category: Optional[str] = "General"
    previous_value: Optional[str] = "Not available"
    latest_value: Optional[str] = "Not available"
    previous_numeric: Optional[float] = None
    latest_numeric: Optional[float] = None
    unit: Optional[str] = "Not available"
    change: str = "Not available"
    percentage_change: str = "Not available"
    trend_direction: str = "Insufficient data" # "Increased", "Decreased", "Stable", "Insufficient data"
    reference_range_status: str = "Not available in source" # "Within available reference range", "Outside available reference range", "Not available in source"
    reference_range_text: Optional[str] = None
    previous_date: Optional[str] = "Not available"
    latest_date: Optional[str] = "Not available"
    source_document_id: Optional[int] = None
    source_document_title: Optional[str] = "Not available"
    source_snippet: Optional[str] = None

class HealthIntelligenceSummary(BaseModel):
    tracked_biomarkers_count: int = 0
    total_measurements_count: int = 0
    recent_changes: List[BiomarkerChange] = []
    outside_range_count: int = 0
    stable_count: int = 0
    increased_count: int = 0
    decreased_count: int = 0

class TrendDataPoint(BaseModel):
    date: str
    numeric_value: float
    observed_value: str
    unit: Optional[str] = None
    flag: str = "normal"
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    document_id: Optional[int] = None
    document_title: Optional[str] = None
    source_snippet: Optional[str] = None

class BiomarkerTrendSeries(BaseModel):
    test_name: str
    canonical_name: str
    category: str
    unit: str
    reference_range_text: Optional[str] = None
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    data_points: List[TrendDataPoint] = []

class CompareReportsRequest(BaseModel):
    document_ids: List[int]

class ReportComparisonItem(BaseModel):
    test_name: str
    canonical_name: Optional[str] = None
    category: Optional[str] = "General"
    unit: str = "Not available"
    baseline_value: str = "Not available"
    baseline_date: str = "Not available"
    baseline_doc_id: Optional[int] = None
    baseline_doc_title: Optional[str] = None
    latest_value: str = "Not available"
    latest_date: str = "Not available"
    latest_doc_id: Optional[int] = None
    latest_doc_title: Optional[str] = None
    change: str = "Not available"
    percentage_change: str = "Not available"
    trend_direction: str = "Insufficient data"
    reference_range_status: str = "Not available in source"
    reference_range_text: Optional[str] = None
    values_by_document: Dict[str, Optional[str]] = {} # doc_id string -> observed_value

class ReportComparisonMatrix(BaseModel):
    compared_documents: List[Dict[str, Any]] = []
    comparisons: List[ReportComparisonItem] = []
    total_tests_compared: int = 0

class TimelineMeasurement(BaseModel):
    test_name: str
    observed_value: str
    unit: Optional[str] = None
    flag: str = "normal"
    reference_range: Optional[str] = None

class TimelinePrescription(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None

class TimelineEvent(BaseModel):
    event_date: str
    document_id: int
    document_title: str
    document_category: str
    doctor_name: Optional[str] = None
    clinic_or_lab: Optional[str] = None
    file_type: str = "PDF"
    measurements: List[TimelineMeasurement] = []
    prescriptions: List[TimelinePrescription] = []
