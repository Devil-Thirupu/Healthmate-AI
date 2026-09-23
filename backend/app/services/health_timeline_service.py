from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.app.models.document import Document
from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.services.health_intelligence_service import health_intelligence_service

class HealthTimelineService:
    """
    HealthMate AI Health Timeline Engine (Phase 14)
    ===============================================
    Constructs an interactive multi-source medical history timeline:
      - Combines Reports, Lab Tests, Prescriptions, Vitals, and Appointments
      - Sorts chronologically
      - Computes previous record comparisons for lab tests
      - Filters by category, date range, and search keyword
      - Preserves full source traceability
    """

    def parse_date_safe(self, date_str: Optional[str]) -> datetime:
        if not date_str or date_str in {"Undated", "Recent", "Unknown", "Not available in source"}:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
        
        # Try various date formats
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%Y-%m-%dT%H:%M:%S"]
        clean_date = date_str.strip().split(" ")[0] if " " in date_str and "-" in date_str else date_str.strip()
        
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_date, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

    def get_health_timeline(
        self,
        db: Session,
        user_id: int,
        category: str = "ALL", # "ALL", "REPORTS", "LAB_TESTS", "PRESCRIPTIONS", "VITALS", "APPOINTMENTS"
        date_range: str = "all", # "30d", "3m", "6m", "1y", "all"
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constructs the comprehensive chronological health timeline with filtering strictly for user_id.
        """
        events: List[Dict[str, Any]] = []

        # Get health intelligence recent changes map for previous comparisons
        summary = health_intelligence_service.get_user_health_intelligence_summary(db, user_id)
        changes_map = {c.get("test_name", "").lower(): c for c in summary.get("recent_changes", [])}

        # 1. Documents (Medical Reports & Imaged Vault Records)
        docs = db.query(Document).filter(Document.user_id == user_id).all()
        doc_map = {d.id: d for d in docs}

        for d in docs:
            d_date = d.document_date or d.created_at.strftime("%Y-%m-%d")
            cat_display = "Lab Report" if d.category == "lab_report" else "Prescription" if d.category == "prescription" else "Diagnostic Record"
            events.append({
                "id": f"doc_{d.id}",
                "event_date": d_date,
                "event_type": "REPORT",
                "title": d.title,
                "summary": f"Uploaded {cat_display} ({d.original_filename})",
                "relevant_value": None,
                "unit": None,
                "previous_value": None,
                "percentage_change": None,
                "trend_direction": None,
                "flag": None,
                "reference_range": None,
                "source_document_id": d.id,
                "source_document_title": d.title,
                "source_page_number": 1,
                "record_id": f"doc_{d.id}",
                "ocr_snippet": d.ocr_raw_text[:250] if d.ocr_raw_text else None,
                "doctor_name": d.doctor_name,
                "clinic_or_lab": d.clinic_or_lab,
                "details": {
                    "document_id": d.id,
                    "category": d.category,
                    "file_size": d.file_size_bytes,
                    "ocr_status": d.ocr_status
                }
            })

        # 2. Lab Tests
        lab_tests = db.query(LabTest).filter(LabTest.user_id == user_id).all()
        for t in lab_tests:
            doc = doc_map.get(t.document_id)
            t_date = t.test_date or (doc.document_date if doc else t.created_at.strftime("%Y-%m-%d"))
            
            c = changes_map.get(t.test_name.lower())
            prev_val = c.get("previous_value") if c else None
            pct_change = c.get("percentage_change") if c else None
            trend = c.get("trend_direction", "Stable") if c else ("First Recorded" if t.flag == "normal" else "Observed")

            events.append({
                "id": f"lab_{t.id}",
                "event_date": t_date,
                "event_type": "LAB_TEST",
                "title": t.test_name,
                "summary": f"Observed {t.test_name}: {t.observed_value} {t.unit or ''}".strip(),
                "relevant_value": t.observed_value,
                "unit": t.unit,
                "previous_value": prev_val,
                "percentage_change": pct_change,
                "trend_direction": trend,
                "flag": t.flag,
                "reference_range": t.reference_range_text,
                "source_document_id": t.document_id,
                "source_document_title": doc.title if doc else "Diagnostic Report",
                "source_page_number": 1,
                "record_id": f"lab_{t.id}",
                "ocr_snippet": t.original_ocr_snippet or f"{t.test_name}: {t.observed_value} {t.unit or ''}",
                "doctor_name": doc.doctor_name if doc else None,
                "clinic_or_lab": doc.clinic_or_lab if doc else t.lab_name,
                "details": {
                    "canonical_name": t.canonical_name,
                    "category": t.test_category,
                    "confidence_score": t.confidence_score
                }
            })

        # 3. Prescriptions
        rxs = db.query(Prescription).filter(Prescription.user_id == user_id).all()
        for rx in rxs:
            doc = doc_map.get(rx.document_id)
            rx_date = rx.prescribed_date or (doc.document_date if doc else rx.created_at.strftime("%Y-%m-%d"))
            dose_str = f" ({rx.dosage})" if rx.dosage else ""
            events.append({
                "id": f"rx_{rx.id}",
                "event_date": rx_date,
                "event_type": "PRESCRIPTION",
                "title": f"Rx {rx.medication_name}",
                "summary": f"Prescribed {rx.medication_name}{dose_str} — {rx.frequency or 'Standard frequency'}",
                "relevant_value": rx.dosage,
                "unit": None,
                "previous_value": None,
                "percentage_change": None,
                "trend_direction": None,
                "flag": None,
                "reference_range": None,
                "source_document_id": rx.document_id,
                "source_document_title": doc.title if doc else "Prescription Record",
                "source_page_number": 1,
                "record_id": f"rx_{rx.id}",
                "ocr_snippet": rx.original_ocr_snippet or f"Rx: {rx.medication_name} {rx.dosage or ''}",
                "doctor_name": rx.doctor_name or (doc.doctor_name if doc else None),
                "clinic_or_lab": doc.clinic_or_lab if doc else None,
                "details": {
                    "medication_name": rx.medication_name,
                    "dosage": rx.dosage,
                    "frequency": rx.frequency,
                    "timing": rx.timing_instructions,
                    "duration": rx.duration
                }
            })

        # 4. Vital Records
        vitals = db.query(VitalRecord).filter(VitalRecord.user_id == user_id).all()
        for v in vitals:
            bp_str = f"BP {v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg" if v.blood_pressure_systolic else "Vitals recorded"
            events.append({
                "id": f"vital_{v.id}",
                "event_date": v.record_date,
                "event_type": "VITALS",
                "title": "Vital Signs Measurement",
                "summary": bp_str,
                "relevant_value": f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}" if v.blood_pressure_systolic else None,
                "unit": "mmHg" if v.blood_pressure_systolic else None,
                "previous_value": None,
                "percentage_change": None,
                "trend_direction": "Stable",
                "flag": "normal",
                "reference_range": "120/80 mmHg",
                "source_document_id": None,
                "source_document_title": "Vital Log Record",
                "source_page_number": 1,
                "record_id": f"vital_{v.id}",
                "ocr_snippet": v.notes,
                "doctor_name": None,
                "clinic_or_lab": None,
                "details": {
                    "heart_rate": v.heart_rate,
                    "blood_glucose": v.blood_glucose_fasting,
                    "spo2": v.oxygen_saturation_spo2
                }
            })

        # 5. Appointment Summaries
        appts = db.query(AppointmentSummary).filter(AppointmentSummary.user_id == user_id).all()
        for a in appts:
            events.append({
                "id": f"appt_{a.id}",
                "event_date": a.visit_date or a.created_at.strftime("%Y-%m-%d"),
                "event_type": "APPOINTMENT",
                "title": f"Appointment Preparation ({a.doctor_specialty or 'General'})",
                "summary": f"Doctor: {a.doctor_name or 'Specialist'} • {len(a.questions_json or [])} questions prepared",
                "relevant_value": None,
                "unit": None,
                "previous_value": None,
                "percentage_change": None,
                "trend_direction": None,
                "flag": None,
                "reference_range": None,
                "source_document_id": None,
                "source_document_title": "Appointment Summary",
                "source_page_number": 1,
                "record_id": f"appt_{a.id}",
                "ocr_snippet": a.reason_for_visit,
                "doctor_name": a.doctor_name,
                "clinic_or_lab": a.clinic_name,
                "details": {
                    "reason_for_visit": a.reason_for_visit,
                    "specialty": a.doctor_specialty
                }
            })

        # Sort chronologically (newest first)
        events.sort(key=lambda x: self.parse_date_safe(x["event_date"]), reverse=True)
        total_events = len(events)

        # Apply Category Filter
        cat_upper = category.upper()
        if cat_upper in {"REPORTS", "REPORT"}:
            events = [e for e in events if e["event_type"] == "REPORT"]
        elif cat_upper in {"LAB_TESTS", "LAB_TEST", "TESTS"}:
            events = [e for e in events if e["event_type"] == "LAB_TEST"]
        elif cat_upper in {"PRESCRIPTIONS", "PRESCRIPTION", "MEDS", "MEDICATIONS"}:
            events = [e for e in events if e["event_type"] == "PRESCRIPTION"]
        elif cat_upper in {"VITALS", "VITAL"}:
            events = [e for e in events if e["event_type"] == "VITALS"]
        elif cat_upper in {"APPOINTMENTS", "APPOINTMENT"}:
            events = [e for e in events if e["event_type"] == "APPOINTMENT"]

        # Apply Date Range Filter
        now_dt = datetime.now(timezone.utc)
        if date_range == "30d":
            cutoff = now_dt - timedelta(days=30)
            events = [e for e in events if self.parse_date_safe(e["event_date"]) >= cutoff or e["event_date"] == now_dt.strftime("%Y-%m-%d")]
        elif date_range == "3m":
            cutoff = now_dt - timedelta(days=90)
            events = [e for e in events if self.parse_date_safe(e["event_date"]) >= cutoff or e["event_date"] == now_dt.strftime("%Y-%m-%d")]
        elif date_range == "6m":
            cutoff = now_dt - timedelta(days=180)
            events = [e for e in events if self.parse_date_safe(e["event_date"]) >= cutoff or e["event_date"] == now_dt.strftime("%Y-%m-%d")]
        elif date_range == "1y":
            cutoff = now_dt - timedelta(days=365)
            events = [e for e in events if self.parse_date_safe(e["event_date"]) >= cutoff or e["event_date"] == now_dt.strftime("%Y-%m-%d")]

        # Apply Search Query
        if search_query and search_query.strip():
            sq = search_query.strip().lower()
            events = [
                e for e in events if
                sq in e["title"].lower() or
                sq in e["summary"].lower() or
                (e["relevant_value"] and sq in e["relevant_value"].lower()) or
                (e["source_document_title"] and sq in e["source_document_title"].lower()) or
                (e["doctor_name"] and sq in e["doctor_name"].lower()) or
                (e["clinic_or_lab"] and sq in e["clinic_or_lab"].lower()) or
                (e["event_date"] and sq in e["event_date"].lower())
            ]

        return {
            "total_events": total_events,
            "filtered_events_count": len(events),
            "category_filter": category,
            "date_range_filter": date_range,
            "search_query": search_query,
            "events": events
        }

health_timeline_service = HealthTimelineService()
