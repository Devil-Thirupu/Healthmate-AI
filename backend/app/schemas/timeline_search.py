from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TimelineEventItem(BaseModel):
    id: str
    event_date: str
    event_type: str # "REPORT", "LAB_TEST", "PRESCRIPTION", "VITALS", "APPOINTMENT"
    title: str
    summary: str
    relevant_value: Optional[str] = None
    unit: Optional[str] = None
    previous_value: Optional[str] = None
    percentage_change: Optional[str] = None
    trend_direction: Optional[str] = None # "Increased", "Decreased", "Stable", "First Recorded", "Observed"
    flag: Optional[str] = None # "normal", "high", "low", "critical"
    reference_range: Optional[str] = None
    source_document_id: Optional[int] = None
    source_document_title: Optional[str] = None
    source_page_number: int = 1
    record_id: Optional[str] = None
    ocr_snippet: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_or_lab: Optional[str] = None
    details: Dict[str, Any] = {}

class TimelineResponse(BaseModel):
    total_events: int
    filtered_events_count: int
    category_filter: str
    date_range_filter: str
    search_query: Optional[str] = None
    events: List[TimelineEventItem] = []

class ExplainReportRequest(BaseModel):
    language: Optional[str] = "en" # "en", "ta", "tanglish"

class ExplainReportResponse(BaseModel):
    document_id: int
    document_title: str
    document_date: Optional[str] = None
    language: str
    report_overview: str
    recorded_values_text: str
    what_changed_text: str
    general_context_text: str
    disclaimer: str
    full_explanation: str
    evidence_status: str
    citations: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []

class GlobalSearchResultItem(BaseModel):
    result_type: str # "LAB_TEST", "PRESCRIPTION", "DOCUMENT", "VITALS", "DOCUMENT_CHUNK"
    title: str
    subtitle: Optional[str] = None
    value: Optional[str] = None
    date: Optional[str] = None
    source_document_id: Optional[int] = None
    source_document_title: Optional[str] = None
    source_page_number: int = 1
    snippet: Optional[str] = None
    relevance_score: float = 1.0

class GlobalSearchResponse(BaseModel):
    query: str
    total_results: int
    structured_count: int
    semantic_count: int
    results: List[GlobalSearchResultItem] = []

class DoctorVisitReportItem(BaseModel):
    id: int
    title: str
    date: Optional[str] = None
    category: str
    extracted_measurements_summary: str

class DoctorVisitMedicationItem(BaseModel):
    id: int
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None
    prescribed_date: Optional[str] = None
    source_document_title: Optional[str] = None
    source_page: int = 1

class DoctorVisitTrendItem(BaseModel):
    test_name: str
    canonical_name: Optional[str] = None
    historical_points: List[Dict[str, Any]] = []
    current_value: str
    unit: Optional[str] = None
    trend_summary: str

class DoctorVisitSummaryResponse(BaseModel):
    patient_name: str
    date_of_visit: str
    recent_reports: List[DoctorVisitReportItem] = []
    current_medications: List[DoctorVisitMedicationItem] = []
    health_trends: List[DoctorVisitTrendItem] = []
    important_measurements: List[Dict[str, Any]] = []
    questions_to_discuss: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
