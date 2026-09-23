from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class AppointmentSummaryGenerateRequest(BaseModel):
    title: Optional[str] = Field("General Medical Consultation Summary", description="Title of the appointment summary")
    date_range_start: Optional[str] = Field(None, description="Start date filter YYYY-MM-DD")
    date_range_end: Optional[str] = Field(None, description="End date filter YYYY-MM-DD")
    selected_document_ids: Optional[List[int]] = Field(None, description="Optional specific document IDs to include")
    selected_test_ids: Optional[List[int]] = Field(None, description="Optional specific lab test IDs to include")
    selected_rx_ids: Optional[List[int]] = Field(None, description="Optional specific prescription IDs to include")

class AppointmentSummaryUpdateRequest(BaseModel):
    title: Optional[str] = None
    generated_questions: Optional[List[str]] = None
    excluded_sections: Optional[List[str]] = None
    custom_notes: Optional[str] = None
    summary_data: Optional[Dict[str, Any]] = None

class AppointmentSummaryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    summary_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AppointmentSummaryListItem(BaseModel):
    id: int
    title: str
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
