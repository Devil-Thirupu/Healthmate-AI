import re
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

health_intelligence_service = HealthIntelligenceService()
