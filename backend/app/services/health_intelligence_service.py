import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.app.models.clinical import LabTest, Prescription, LabFlag
from backend.app.models.document import Document
from backend.app.core.logging import logger

class HealthIntelligenceService:
    """
    Health Intelligence Engine & Report Comparison Service.
    
    Safety & Compliance Rules:
      1. Descriptive only: NO disease diagnosis, NO predictions, NO drug recommendations.
      2. Strict Unit Safety: Compare only when units are identical (case-insensitive string match).
      3. Zero-Hallucination Mathematics:
         - Percentage change: ((latest - previous) / previous) * 100
         - If previous == 0 -> percentage change = "Not available" (never divide by zero).
         - Missing/non-numeric values -> "Not available".
      4. Neutral Trend Terminology:
         - "Increased": latest > previous
         - "Decreased": latest < previous
         - "Stable": relative difference <= 1.0% (or absolute difference < 0.001)
         - "Insufficient data": when only 1 measurement exists or values cannot be compared.
      5. Reference Ranges:
         - "Within available reference range"
         - "Outside available reference range"
         - "Not available in source"
    """

    STABILITY_TOLERANCE_PCT = 1.0 # 1.0% relative tolerance for 'Stable' classification
    STABILITY_ABSOLUTE_EPS = 0.001 # Absolute tolerance for floating point comparisons

    def are_units_compatible(self, u1: Optional[str], u2: Optional[str]) -> bool:
        """
        Validates unit compatibility.
        Only compares measurements with identical units (case-insensitive).
        Never invents conversions.
        """
        if not u1 or not u2:
            return False
        clean1 = u1.strip().lower()
        clean2 = u2.strip().lower()
        if not clean1 or not clean2 or clean1 in {"n/a", "none", "not available"} or clean2 in {"n/a", "none", "not available"}:
            return False
        return clean1 == clean2

    def calculate_change(
        self,
        prev_numeric: Optional[float],
        latest_numeric: Optional[float],
        prev_unit: Optional[str],
        latest_unit: Optional[str]
    ) -> Tuple[str, str, str]:
        """
        Calculates numerical difference, percentage change, and trend direction.
        Returns: (change_str, percentage_change_str, trend_direction)
        """
        # If either value is missing
        if prev_numeric is None or latest_numeric is None:
            return "Not available", "Not available", "Insufficient data"

        # Unit compatibility check
        if not self.are_units_compatible(prev_unit, latest_unit):
            return "Incompatible units", "Not available", "Insufficient data"

        # Calculate numerical difference
        delta = latest_numeric - prev_numeric
        unit_str = f" {latest_unit.strip()}" if latest_unit else ""

        if delta > 0:
            change_str = f"+{delta:.2f}".rstrip('0').rstrip('.') + unit_str
        elif delta < 0:
            change_str = f"{delta:.2f}".rstrip('0').rstrip('.') + unit_str
        else:
            change_str = f"0.0" + unit_str

        # Percentage change calculation with Zero-Division protection
        if prev_numeric == 0:
            pct_str = "Not available"
        else:
            pct_val = ((latest_numeric - prev_numeric) / abs(prev_numeric)) * 100.0
            if pct_val > 0:
                pct_str = f"+{pct_val:.2f}%"
            elif pct_val < 0:
                pct_str = f"{pct_val:.2f}%"
            else:
                pct_str = "0.00%"

        # Trend direction determination with 1% relative tolerance
        if abs(delta) < self.STABILITY_ABSOLUTE_EPS:
            trend = "Stable"
        elif prev_numeric != 0 and abs(((latest_numeric - prev_numeric) / abs(prev_numeric)) * 100.0) <= self.STABILITY_TOLERANCE_PCT:
            trend = "Stable"
        elif delta > 0:
            trend = "Increased"
        else:
            trend = "Decreased"

        return change_str, pct_str, trend

    def evaluate_reference_range(
        self,
        numeric_val: Optional[float],
        ref_min: Optional[float],
        ref_max: Optional[float],
        ref_text: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Evaluates whether a numeric value is within available reference range.
        Returns: (status_str, reference_range_display_text)
        """
        # If no numeric reference bounds exist
        if ref_min is None and ref_max is None:
            if ref_text and ref_text.strip() and ref_text.lower() not in {"n/a", "none", "null"}:
                return "Range available (text)", ref_text.strip()
            return "Not available in source", None

        # Build display text if not already provided
        display_text = ref_text
        if not display_text:
            if ref_min is not None and ref_max is not None:
                display_text = f"{ref_min} - {ref_max}"
            elif ref_min is not None:
                display_text = f">= {ref_min}"
            elif ref_max is not None:
                display_text = f"<= {ref_max}"

        if numeric_val is None:
            return "Not available in source", display_text

        # Evaluate bounds
        is_outside = False
        if ref_min is not None and numeric_val < ref_min:
            is_outside = True
        if ref_max is not None and numeric_val > ref_max:
            is_outside = True

        status = "Outside available reference range" if is_outside else "Within available reference range"
        return status, display_text

    def get_user_health_intelligence_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Computes the complete Health Intelligence summary for a patient:
        - Groups all historical lab tests by canonical_name / test_name
        - Sorts chronologically
        - Computes baseline-to-latest or previous-to-latest changes
        - Formulates descriptive analytics cards with full source traceability
        """
        # Fetch all lab tests for user ordered chronologically
        lab_tests = db.query(LabTest).filter(
            LabTest.user_id == user_id
        ).order_by(asc(LabTest.test_date), asc(LabTest.created_at)).all()

        if not lab_tests:
            return {
                "tracked_biomarkers_count": 0,
                "total_measurements_count": 0,
                "recent_changes": [],
                "outside_range_count": 0,
                "stable_count": 0,
                "increased_count": 0,
                "decreased_count": 0
            }

        # Group tests by canonical key (or lowercase test_name)
        groups: Dict[str, List[LabTest]] = {}
        for test in lab_tests:
            key = (test.canonical_name or test.test_name).strip().lower()
            if key not in groups:
                groups[key] = []
            groups[key].append(test)

        recent_changes = []
        outside_count = 0
        stable_count = 0
        inc_count = 0
        dec_count = 0

        for key, tests in groups.items():
            latest = tests[-1]
            prev = tests[-2] if len(tests) >= 2 else None

            # Evaluate reference range for latest
            ref_status, ref_text = self.evaluate_reference_range(
                numeric_val=latest.numeric_value,
                ref_min=latest.reference_range_min,
                ref_max=latest.reference_range_max,
                ref_text=latest.reference_range_text
            )

            if ref_status == "Outside available reference range" or latest.flag in {LabFlag.HIGH.value, LabFlag.LOW.value, LabFlag.CRITICAL.value}:
                outside_count += 1

            # Fetch source document info
            doc = db.query(Document).filter(Document.id == latest.document_id).first() if latest.document_id else None
            prev_doc = db.query(Document).filter(Document.id == prev.document_id).first() if (prev and prev.document_id) else None

            if prev:
                change_str, pct_str, trend = self.calculate_change(
                    prev_numeric=prev.numeric_value,
                    latest_numeric=latest.numeric_value,
                    prev_unit=prev.unit,
                    latest_unit=latest.unit
                )
                prev_val_str = f"{prev.observed_value} {prev.unit or ''}".strip()
                prev_date_str = prev.test_date or (prev_doc.document_date if prev_doc else "Undated")
            else:
                change_str = "Not available"
                pct_str = "Not available"
                trend = "Insufficient data"
                prev_val_str = "Not available"
                prev_date_str = "Not available"

            if trend == "Increased":
                inc_count += 1
            elif trend == "Decreased":
                dec_count += 1
            elif trend == "Stable":
                stable_count += 1

            latest_val_str = f"{latest.observed_value} {latest.unit or ''}".strip()
            latest_date_str = latest.test_date or (doc.document_date if doc else "Undated")

            recent_changes.append({
                "test_name": latest.test_name,
                "canonical_name": latest.canonical_name or key,
                "test_category": latest.test_category or "General",
                "previous_value": prev_val_str,
                "latest_value": latest_val_str,
                "previous_numeric": prev.numeric_value if prev else None,
                "latest_numeric": latest.numeric_value,
                "unit": latest.unit or "Not available",
                "change": change_str,
                "percentage_change": pct_str,
                "trend_direction": trend,
                "reference_range_status": ref_status,
                "reference_range_text": ref_text,
                "previous_date": prev_date_str,
                "latest_date": latest_date_str,
                "source_document_id": latest.document_id,
                "source_document_title": doc.title if doc else (doc.original_filename if doc else "Uploaded Document"),
                "source_snippet": latest.original_ocr_snippet
            })

        return {
            "tracked_biomarkers_count": len(groups),
            "total_measurements_count": len(lab_tests),
            "recent_changes": recent_changes,
            "outside_range_count": outside_count,
            "stable_count": stable_count,
            "increased_count": inc_count,
            "decreased_count": dec_count
        }

    def get_biomarker_trends(self, db: Session, user_id: int, canonical_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves historical time-series data for biomarkers, formatted for Recharts line charts.
        Never combines incompatible units into the same trend series.
        """
        query = db.query(LabTest).filter(LabTest.user_id == user_id)
        if canonical_name:
            query = query.filter(
                (LabTest.canonical_name == canonical_name) | (LabTest.test_name.ilike(f"%{canonical_name}%"))
            )
        lab_tests = query.order_by(asc(LabTest.test_date), asc(LabTest.created_at)).all()

        # Group by canonical_name + unit to ensure strict unit safety
        series_groups: Dict[str, Dict[str, Any]] = {}

        for test in lab_tests:
            if test.numeric_value is None:
                continue

            c_name = test.canonical_name or test.test_name
            unit_key = (test.unit or "standard").strip().lower()
            group_key = f"{c_name.lower()}___{unit_key}"

            if group_key not in series_groups:
                series_groups[group_key] = {
                    "test_name": test.test_name,
                    "canonical_name": c_name,
                    "category": test.test_category or "General",
                    "unit": test.unit or "Not available",
                    "reference_range_text": test.reference_range_text,
                    "reference_range_min": test.reference_range_min,
                    "reference_range_max": test.reference_range_max,
                    "data_points": []
                }

            doc = db.query(Document).filter(Document.id == test.document_id).first() if test.document_id else None
            date_str = test.test_date or (doc.document_date if doc else test.created_at.strftime("%Y-%m-%d"))

            series_groups[group_key]["data_points"].append({
                "date": date_str,
                "numeric_value": test.numeric_value,
                "observed_value": test.observed_value,
                "unit": test.unit,
                "flag": test.flag,
                "reference_range_min": test.reference_range_min,
                "reference_range_max": test.reference_range_max,
                "document_id": test.document_id,
                "document_title": doc.title if doc else "Report",
                "source_snippet": test.original_ocr_snippet
            })

        return list(series_groups.values())

    def compare_selected_reports(self, db: Session, user_id: int, document_ids: List[int]) -> Dict[str, Any]:
        """
        Cross-tabulates and compares biomarkers across 2 or more selected medical reports.
        Enforces user ownership on all document_ids.
        """
        if not document_ids or len(document_ids) < 2:
            return {
                "compared_documents": [],
                "comparisons": [],
                "total_tests_compared": 0
            }

        # 1. Fetch documents in chronological order
        docs = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == user_id
        ).order_by(asc(Document.document_date), asc(Document.created_at)).all()

        if len(docs) < 2:
            return {
                "compared_documents": [{"id": d.id, "title": d.title, "date": d.document_date} for d in docs],
                "comparisons": [],
                "total_tests_compared": 0
            }

        ordered_doc_ids = [d.id for d in docs]
        doc_map = {d.id: d for d in docs}

        # 2. Fetch all lab tests belonging to these documents
        lab_tests = db.query(LabTest).filter(
            LabTest.document_id.in_(ordered_doc_ids),
            LabTest.user_id == user_id
        ).all()

        # 3. Group by test canonical key
        test_matrix: Dict[str, Dict[int, LabTest]] = {}
        for test in lab_tests:
            key = (test.canonical_name or test.test_name).strip().lower()
            if key not in test_matrix:
                test_matrix[key] = {}
            test_matrix[key][test.document_id] = test

        comparisons = []

        for key, doc_tests in test_matrix.items():
            # Find earliest available test and latest available test among selected docs
            present_doc_ids = [did for did in ordered_doc_ids if did in doc_tests]
            if not present_doc_ids:
                continue

            first_doc_id = present_doc_ids[0]
            latest_doc_id = present_doc_ids[-1]

            first_test = doc_tests[first_doc_id]
            latest_test = doc_tests[latest_doc_id]

            first_doc = doc_map[first_doc_id]
            latest_doc = doc_map[latest_doc_id]

            if len(present_doc_ids) >= 2:
                change_str, pct_str, trend = self.calculate_change(
                    prev_numeric=first_test.numeric_value,
                    latest_numeric=latest_test.numeric_value,
                    prev_unit=first_test.unit,
                    latest_unit=latest_test.unit
                )
            else:
                change_str = "Not available"
                pct_str = "Not available"
                trend = "Insufficient data"

            ref_status, ref_text = self.evaluate_reference_range(
                numeric_val=latest_test.numeric_value,
                ref_min=latest_test.reference_range_min,
                ref_max=latest_test.reference_range_max,
                ref_text=latest_test.reference_range_text
            )

            # Build values_by_document map
            values_by_doc = {}
            for did in ordered_doc_ids:
                if did in doc_tests:
                    t = doc_tests[did]
                    values_by_doc[str(did)] = f"{t.observed_value} {t.unit or ''}".strip()
                else:
                    values_by_doc[str(did)] = "Not tested"

            comparisons.append({
                "test_name": latest_test.test_name,
                "canonical_name": latest_test.canonical_name or key,
                "category": latest_test.test_category or "General",
                "unit": latest_test.unit or "Not available",
                "baseline_value": f"{first_test.observed_value} {first_test.unit or ''}".strip(),
                "baseline_date": first_test.test_date or (first_doc.document_date or "Undated"),
                "baseline_doc_id": first_doc_id,
                "baseline_doc_title": first_doc.title,
                "latest_value": f"{latest_test.observed_value} {latest_test.unit or ''}".strip(),
                "latest_date": latest_test.test_date or (latest_doc.document_date or "Undated"),
                "latest_doc_id": latest_doc_id,
                "latest_doc_title": latest_doc.title,
                "change": change_str,
                "percentage_change": pct_str,
                "trend_direction": trend,
                "reference_range_status": ref_status,
                "reference_range_text": ref_text,
                "values_by_document": values_by_doc
            })

        return {
            "compared_documents": [
                {
                    "id": d.id,
                    "title": d.title,
                    "date": d.document_date or "Undated",
                    "clinic": d.clinic_or_lab,
                    "category": d.category
                } for d in docs
            ],
            "comparisons": comparisons,
            "total_tests_compared": len(comparisons)
        }

    def get_chronological_timeline(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Constructs a complete chronological medical history timeline:
        - Lists documents ordered by date
        - Shows extracted lab tests and prescriptions for each event
        - Preserves full source traceability
        """
        docs = db.query(Document).filter(
            Document.user_id == user_id
        ).order_by(desc(Document.document_date), desc(Document.created_at)).all()

        timeline = []
        for doc in docs:
            # Fetch lab tests for this doc
            tests = db.query(LabTest).filter(LabTest.document_id == doc.id).all()
            measurements = [
                {
                    "test_name": t.test_name,
                    "observed_value": f"{t.observed_value} {t.unit or ''}".strip(),
                    "unit": t.unit,
                    "flag": t.flag,
                    "reference_range": t.reference_range_text
                } for t in tests
            ]

            # Fetch prescriptions for this doc
            rxs = db.query(Prescription).filter(Prescription.document_id == doc.id).all()
            prescriptions = [
                {
                    "medication_name": rx.medication_name,
                    "dosage": rx.dosage or "Not available in source",
                    "frequency": rx.frequency or "Not available in source",
                    "duration": rx.duration or "Not available in source"
                } for rx in rxs
            ]

            ext = doc.stored_filename.split('.')[-1].upper() if '.' in doc.stored_filename else "FILE"

            timeline.append({
                "event_date": doc.document_date or doc.created_at.strftime("%Y-%m-%d"),
                "document_id": doc.id,
                "document_title": doc.title,
                "document_category": doc.category,
                "doctor_name": doc.doctor_name,
                "clinic_or_lab": doc.clinic_or_lab,
                "file_type": ext,
                "measurements": measurements,
                "prescriptions": prescriptions
            })

        return timeline

    def explain_report(
        self,
        db: Session,
        user_id: int,
        document_id: int,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generates the structured "Explain My Report" response (Phase 14):
        - REPORT OVERVIEW
        - YOUR RECORDED VALUES
        - WHAT CHANGED
        - WHAT THE TEST GENERALLY MEASURES
        - IMPORTANT (Disclaimer)
        - SOURCES
        Applies Evidence Guard strictly and supports English, Tamil, and Tanglish.
        """
        from backend.app.services.evidence_guard_service import evidence_guard_service
        from backend.app.services.multilingual_explanation_service import multilingual_explanation_service

        doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not doc:
            return None

        lab_tests = db.query(LabTest).filter(LabTest.document_id == document_id, LabTest.user_id == user_id).all()
        summary = self.get_user_health_intelligence_summary(db, user_id)
        recent_changes_map = {c.get("test_name", "").lower(): c for c in summary.get("recent_changes", [])}

        lang = multilingual_explanation_service.normalize_language(language)

        # 1. REPORT OVERVIEW
        count = len(lab_tests)
        if lang == "ta":
            overview = f"இந்த மருத்துவ அறிக்கை {count} பிரித்தெடுக்கப்பட்ட ஆய்வக அளவீடுகளைக் கொண்டுள்ளது."
        elif lang == "tanglish":
            overview = f"Indha medical report-la {count} extracted lab measurements irukku."
        else:
            overview = f"This report contains {count} extracted lab measurement(s)."

        # 2. YOUR RECORDED VALUES
        val_lines = []
        citations = []
        for t in lab_tests:
            val_lines.append(multilingual_explanation_service.format_lab_item(
                test_name=t.test_name,
                value=t.observed_value,
                unit=t.unit,
                date=t.test_date or doc.document_date or "Recent",
                flag=t.flag,
                language=lang
            ))
            citations.append({
                "source_type": "USER_STRUCTURED_RECORD",
                "source_name": doc.title,
                "document_id": doc.id,
                "page_number": 1,
                "text_snippet": f"{t.test_name}: {t.observed_value} {t.unit or ''} (Flag: {t.flag})",
                "relevance_score": 1.0
            })
        recorded_values_text = "\n".join(val_lines) if val_lines else "No specific lab measurements found."

        # 3. WHAT CHANGED
        change_lines = []
        for t in lab_tests:
            c = recent_changes_map.get(t.test_name.lower())
            if c and c.get("previous_value") is not None:
                change_lines.append(f"• {t.test_name}: {c.get('previous_value')} → {c.get('latest_value')} ({c.get('percentage_change')}) [{c.get('trend_direction')}]")
            else:
                change_lines.append(f"• {t.test_name}: {t.observed_value} {t.unit or ''} (First recorded measurement)")
        what_changed_text = "\n".join(change_lines) if change_lines else "No comparison available."

        # 4. WHAT THE TEST GENERALLY MEASURES
        if lang == "ta":
            general_context = "பொது மருத்துவ வழிகாட்டலின்படி, இந்த இரத்தப் பரிசோதனைகள் உடலின் வளர்சிதை மாற்றம், இரத்த அணுக்களின் ஆரோக்கியம் மற்றும் உறுப்புகளின் சமநிலையை மதிப்பிட உதவுகின்றன."
        elif lang == "tanglish":
            general_context = "General medical knowledge padi, indha lab tests ungal body-oda metabolic status, blood cell balance matrum vital organ function-ai review panna use aagudhu."
        else:
            general_context = "According to general clinical references, these diagnostic panels evaluate metabolic equilibrium, blood cell indices, and organ function."

        # 5. IMPORTANT
        disclaimer = multilingual_explanation_service.format_disclaimer(lang)

        # Build combined full explanation
        full_sections = [
            f"REPORT OVERVIEW\n{overview}\n",
            f"YOUR RECORDED VALUES\n{recorded_values_text}\n",
            f"WHAT CHANGED\n{what_changed_text}\n",
            f"WHAT THE TEST GENERALLY MEASURES\n{general_context}\n",
            f"IMPORTANT\n{disclaimer}\n",
            f"SOURCES\n{doc.title} — Page 1"
        ]
        full_text = "\n".join(full_sections)
        guarded_text = evidence_guard_service.sanitize_and_guard_response(
            answer=full_text,
            query_type="PATIENT_FACTUAL",
            has_patient_records=bool(lab_tests),
            is_cause_inquiry=False,
            language=lang
        )

        return {
            "document_id": doc.id,
            "document_title": doc.title,
            "document_date": doc.document_date,
            "language": lang,
            "report_overview": overview,
            "recorded_values_text": recorded_values_text,
            "what_changed_text": what_changed_text,
            "general_context_text": general_context,
            "disclaimer": disclaimer,
            "full_explanation": guarded_text,
            "evidence_status": "SUPPORTED" if lab_tests else "INSUFFICIENT",
            "citations": citations,
            "sources": citations
        }

    def get_doctor_visit_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Aggregates Doctor Visit Mode summary (Phase 14):
        - Recent reports
        - Current medications
        - Health trends
        - Important measurements
        - Questions to discuss
        - Sources
        """
        from backend.app.models.user import User
        from backend.app.models.appointment_summary import AppointmentSummary

        user = db.query(User).filter(User.id == user_id).first()
        patient_name = user.full_name if user else "Patient"

        # 1. Recent Reports
        docs = db.query(Document).filter(Document.user_id == user_id).order_by(desc(Document.created_at)).limit(5).all()
        recent_reports = []
        for d in docs:
            tests = db.query(LabTest).filter(LabTest.document_id == d.id).all()
            summary_str = f"{len(tests)} measurement(s) extracted" if tests else "Archived health document"
            recent_reports.append({
                "id": d.id,
                "title": d.title,
                "date": d.document_date or d.created_at.strftime("%Y-%m-%d"),
                "category": d.category,
                "extracted_measurements_summary": summary_str
            })

        # 2. Current Medications
        rxs = db.query(Prescription).filter(Prescription.user_id == user_id).order_by(desc(Prescription.created_at)).limit(10).all()
        current_medications = []
        for rx in rxs:
            doc = db.query(Document).filter(Document.id == rx.document_id).first() if rx.document_id else None
            current_medications.append({
                "id": rx.id,
                "medicine_name": rx.medication_name,
                "dosage": rx.dosage or "Prescribed",
                "frequency": rx.frequency or "Standard",
                "timing": rx.timing_instructions or "As prescribed",
                "prescribed_date": rx.prescribed_date or (doc.document_date if doc else "Recent"),
                "source_document_title": doc.title if doc else "Prescription Record",
                "source_page": 1
            })

        # 3. Health Trends
        trend_series = self.get_biomarker_trends(db, user_id)
        health_trends = []
        for ts in trend_series[:4]:
            pts = ts.get("points", [])
            curr_val = pts[-1]["observed_value"] if pts else "Not available"
            trend_summary = f"{len(pts)} record(s) tracked"
            if len(pts) >= 2:
                trend_summary = f"{pts[0]['observed_value']} → {pts[-1]['observed_value']} {ts.get('unit', '')}"
            health_trends.append({
                "test_name": ts.get("display_name", ts.get("canonical_name")),
                "canonical_name": ts.get("canonical_name"),
                "historical_points": pts,
                "current_value": curr_val,
                "unit": ts.get("unit"),
                "trend_summary": trend_summary
            })

        # 4. Important / Out-of-range Measurements
        all_tests = db.query(LabTest).filter(LabTest.user_id == user_id).order_by(desc(LabTest.created_at)).all()
        important_measurements = []
        for t in all_tests:
            if t.flag in {"high", "low", "critical", "abnormal"}:
                important_measurements.append({
                    "test_name": t.test_name,
                    "value": f"{t.observed_value} {t.unit or ''}".strip(),
                    "flag": t.flag.upper(),
                    "reference_range": t.reference_range_text,
                    "date": t.test_date or "Recent"
                })
            if len(important_measurements) >= 5:
                break

        # 5. Questions to Discuss (from Appointment Preparation)
        appt = db.query(AppointmentSummary).filter(AppointmentSummary.user_id == user_id).order_by(desc(AppointmentSummary.created_at)).first()
        questions = appt.questions_json if appt and appt.questions_json else [
            {"id": "q1", "question_text": "Can you help me understand the changes in my latest blood test results?", "category": "General", "priority": "HIGH"},
            {"id": "q2", "question_text": "Are my current prescription medications still appropriate?", "category": "Medication", "priority": "MEDIUM"}
        ]

        # 6. Sources
        sources = [
            {"title": d.title, "document_id": d.id, "page": 1} for d in docs[:5]
        ]

        return {
            "patient_name": patient_name,
            "date_of_visit": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "recent_reports": recent_reports,
            "current_medications": current_medications,
            "health_trends": health_trends,
            "important_measurements": important_measurements,
            "questions_to_discuss": questions,
            "sources": sources
        }

health_intelligence_service = HealthIntelligenceService()
