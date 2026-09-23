from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class MedicationReminderBase(BaseModel):
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None
    scheduled_time: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    enabled: bool = True
    page_number: int = 1

class MedicationReminderCreate(MedicationReminderBase):
    prescription_id: Optional[int] = None
    document_id: Optional[int] = None

class MedicationReminderUpdate(BaseModel):
    scheduled_time: Optional[str] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None
    snooze_minutes: Optional[int] = None

class SnoozeReminderRequest(BaseModel):
    snooze_minutes: int = Field(default=30, ge=5, le=1440)

class MedicationReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    prescription_id: Optional[int] = None
    document_id: Optional[int] = None
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None
    scheduled_time: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page_number: int = 1
    status: str
    enabled: bool
    source_document_title: Optional[str] = None
    snooze_until: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class MedicationScheduleSlot(BaseModel):
    time_slot: str # "Morning", "Afternoon", "Night", "Unscheduled"
    display_time: str # "8:00 AM", "1:00 PM", "8:00 PM", or "Timing not specified in the available prescription."
    reminders: List[MedicationReminderOut] = []

class MedicationScheduleOut(BaseModel):
    date: str
    total_active_reminders: int
    completed_count: int
    remaining_count: int
    morning: List[MedicationReminderOut] = []
    afternoon: List[MedicationReminderOut] = []
    night: List[MedicationReminderOut] = []
    unspecified: List[MedicationReminderOut] = []

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    message: str
    related_resource_type: Optional[str] = None
    related_resource_id: Optional[str] = None
    is_read: bool
    created_at: datetime

class NotificationSummaryOut(BaseModel):
    unread_count: int
    notifications: List[NotificationOut] = []
    today_reminders_count: int = 0
    upcoming_reminders_count: int = 0

class DailyBiomarkerInsight(BaseModel):
    test_name: str
    canonical_name: Optional[str] = None
    latest_value: str
    unit: Optional[str] = None
    date: Optional[str] = None
    previous_value: Optional[str] = None
    percentage_change: Optional[str] = None
    trend_direction: str # "Increased", "Decreased", "Stable", "Insufficient data"
    source_document_id: Optional[int] = None
    source_document_title: Optional[str] = None

class DailyNutritionIdea(BaseModel):
    food_name: str
    common_name: Optional[str] = None
    calories: Optional[float] = None
    carbohydrate_g: Optional[float] = None
    fiber_g: Optional[float] = None
    protein_g: Optional[float] = None
    source_attribution: str = "USDA FoodData Central"
    disclaimer: str = "General nutrition information based on USDA data. Discuss dietary changes with a qualified healthcare professional when you have medical conditions or dietary restrictions."

class DailyHealthInsightsOut(BaseModel):
    date: str
    reminders_remaining_today: int
    reminders_completed_today: int
    today_reminders: List[MedicationReminderOut] = []
    latest_biomarkers: List[DailyBiomarkerInsight] = []
    nutrition_ideas: List[DailyNutritionIdea] = []
    recent_prescription_title: Optional[str] = None
    recent_prescription_id: Optional[int] = None
    recent_report_title: Optional[str] = None
    recent_report_id: Optional[int] = None
    appointment_prep_count: int = 0

class ReportInsightItem(BaseModel):
    test_name: str
    latest_value: str
    unit: Optional[str] = None
    previous_value: Optional[str] = None
    percentage_change: Optional[str] = None
    trend_direction: str
    has_previous_comparison: bool

class ReportInsightCardOut(BaseModel):
    document_id: int
    document_title: str
    document_date: Optional[str] = None
    total_measurements_extracted: int
    measurements_with_comparison: int
    measurements_without_comparison: int
    insights: List[ReportInsightItem] = []
