import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.clinical import LabTest, Prescription, VitalRecord, LabFlag
from backend.app.models.rag import RAGChunk
from backend.app.services.health_intelligence_service import health_intelligence_service
from backend.app.services.evidence_guard_service import evidence_guard_service
from backend.app.schemas.appointment_summary import (
    AppointmentSummaryGenerateRequest,
    AppointmentSummaryUpdateRequest
)

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for Page X of Y numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        footer_text = f"HealthMate AI — Appointment Preparation & Health Summary  |  Page {self._pageNumber} of {page_count}"
        self.drawCentredString(letter[0] / 2.0, 30, footer_text)
        self.restoreState()


class AppointmentSummaryService:
    """
    Service for generating, customizing, and rendering Appointment Preparation & Health Summary PDFs.
    Strictly user-isolated and evidence-grounded.
    """

    DISCLAIMER_TEXT = (
        "HEALTHMATE AI NOTICE: This appointment summary is an automated organization of your existing personal health records "
        "intended for consultation preparation. It is NOT a medical diagnosis, prognosis, treatment plan, or prescription recommendation. "
        "Please discuss all observations with your qualified healthcare professional."
    )

    def generate_summary(
        self,
        db: Session,
        user_id: int,
        req: AppointmentSummaryGenerateRequest
    ) -> AppointmentSummary:
        """
        Gathers user records, executes Health Intelligence comparison, drafts grounded questions,
        and saves an AppointmentSummary artifact.
        """
        user = db.query(User).filter(User.id == user_id).first()

        # 1. Fetch user-isolated documents
        doc_query = db.query(Document).filter(Document.user_id == user_id)
        if req.selected_document_ids:
            doc_query = doc_query.filter(Document.id.in_(req.selected_document_ids))
        docs = doc_query.order_by(desc(Document.document_date), desc(Document.created_at)).all()

        recent_docs_data = [
            {
                "id": d.id,
                "title": d.title or d.original_filename,
                "original_filename": d.original_filename,
                "category": d.category,
                "document_date": d.document_date or "Undated",
                "created_at": d.created_at.strftime("%Y-%m-%d") if d.created_at else "Undated"
            }
            for d in docs
        ]

        # 2. Fetch user-isolated lab tests
        test_query = db.query(LabTest).filter(LabTest.user_id == user_id)
        if req.selected_test_ids:
            test_query = test_query.filter(LabTest.id.in_(req.selected_test_ids))
        lab_tests = test_query.order_by(desc(LabTest.test_date), desc(LabTest.created_at)).all()

        # Group lab tests by canonical name for trend analysis
        grouped_tests: Dict[str, List[LabTest]] = {}
        for t in lab_tests:
            key = (t.canonical_name or t.test_name).strip().lower()
            grouped_tests.setdefault(key, []).append(t)

        lab_measurements_data = []
        health_trends_data = []

        for key, t_list in grouped_tests.items():
            # Sort ascending by date for chronological calculation
            chronological = sorted(t_list, key=lambda x: (x.test_date or "", x.created_at or datetime.min))
            latest = chronological[-1]
            previous = chronological[-2] if len(chronological) >= 2 else None

            doc = db.query(Document).filter(Document.id == latest.document_id).first() if latest.document_id else None
            doc_name = doc.title if doc else (doc.original_filename if doc else "Uploaded Report")

            if previous:
                change_str, pct_str, trend_dir = health_intelligence_service.calculate_change(
                    prev_numeric=previous.numeric_value,
                    latest_numeric=latest.numeric_value,
                    prev_unit=previous.unit,
                    latest_unit=latest.unit
                )
                ref_status, _ = health_intelligence_service.evaluate_reference_range(
                    numeric_val=latest.numeric_value,
                    ref_min=latest.reference_range_min,
                    ref_max=latest.reference_range_max,
                    ref_text=latest.reference_range_text
                )
                
                measurement_entry = {
                    "id": latest.id,
                    "test_name": latest.test_name,
                    "latest_value": f"{latest.observed_value} {latest.unit or ''}".strip(),
                    "previous_value": f"{previous.observed_value} {previous.unit or ''}".strip(),
                    "change": change_str,
                    "percentage_change": pct_str,
                    "trend_direction": trend_dir,
                    "flag": latest.flag,
                    "reference_range": latest.reference_range_text or "Not available",
                    "reference_status": ref_status,
                    "date": latest.test_date or "Undated",
                    "previous_date": previous.test_date or "Undated",
                    "source_document": doc_name,
                    "document_id": latest.document_id,
                    "page_number": 1
                }
                lab_measurements_data.append(measurement_entry)

                if trend_dir in ["Increased", "Decreased"] or latest.flag in [LabFlag.HIGH.value, LabFlag.LOW.value, LabFlag.CRITICAL.value, LabFlag.ABNORMAL.value]:
                    health_trends_data.append({
                        "test_name": latest.test_name,
                        "observation": f"{latest.test_name} {trend_dir.lower()} from {previous.observed_value} {previous.unit or ''} ({previous.test_date or 'prev'}) to {latest.observed_value} {latest.unit or ''} ({latest.test_date or 'latest'}) [{pct_str}].",
                        "status": latest.flag.upper(),
                        "source_document": doc_name
                    })
            else:
                ref_status, _ = health_intelligence_service.evaluate_reference_range(
                    numeric_val=latest.numeric_value,
                    ref_min=latest.reference_range_min,
                    ref_max=latest.reference_range_max,
                    ref_text=latest.reference_range_text
                )
                measurement_entry = {
                    "id": latest.id,
                    "test_name": latest.test_name,
                    "latest_value": f"{latest.observed_value} {latest.unit or ''}".strip(),
                    "previous_value": "No previous record",
                    "change": "N/A (Single record)",
                    "percentage_change": "N/A",
                    "trend_direction": "Baseline",
                    "flag": latest.flag,
                    "reference_range": latest.reference_range_text or "Not available",
                    "reference_status": ref_status,
                    "date": latest.test_date or "Undated",
                    "previous_date": "N/A",
                    "source_document": doc_name,
                    "document_id": latest.document_id,
                    "page_number": 1
                }
                lab_measurements_data.append(measurement_entry)

                if latest.flag in [LabFlag.HIGH.value, LabFlag.LOW.value, LabFlag.CRITICAL.value, LabFlag.ABNORMAL.value]:
                    health_trends_data.append({
                        "test_name": latest.test_name,
                        "observation": f"{latest.test_name} recorded as {latest.observed_value} {latest.unit or ''} on {latest.test_date or 'latest'}, which is flagged as {latest.flag.upper()}.",
                        "status": latest.flag.upper(),
                        "source_document": doc_name
                    })

        # 3. Fetch user-isolated prescriptions
        rx_query = db.query(Prescription).filter(Prescription.user_id == user_id)
        if req.selected_rx_ids:
            rx_query = rx_query.filter(Prescription.id.in_(req.selected_rx_ids))
        rxs = rx_query.order_by(desc(Prescription.prescribed_date), desc(Prescription.created_at)).all()

        prescriptions_data = []
        for rx in rxs:
            doc = db.query(Document).filter(Document.id == rx.document_id).first() if rx.document_id else None
            doc_name = doc.title if doc else (doc.original_filename if doc else "Prescription Document")
            prescriptions_data.append({
                "id": rx.id,
                "medication_name": rx.medication_name,
                "dosage": rx.dosage or "Standard",
                "frequency": rx.frequency or "As directed",
                "timing_instructions": rx.timing_instructions or "As directed",
                "duration": rx.duration or "Ongoing",
                "doctor_name": rx.doctor_name or "Treating Physician",
                "prescribed_date": rx.prescribed_date or "Undated",
                "source_document": doc_name,
                "document_id": rx.document_id,
                "page_number": 1
            })

        # 4. Fetch user-isolated vitals
        vitals = db.query(VitalRecord).filter(VitalRecord.user_id == user_id).order_by(desc(VitalRecord.record_date)).limit(5).all()
        vitals_data = [
            {
                "id": v.id,
                "record_date": v.record_date,
                "bp": f"{v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg" if v.blood_pressure_systolic and v.blood_pressure_diastolic else "N/A",
                "heart_rate": f"{v.heart_rate} bpm" if v.heart_rate else "N/A",
                "glucose_fasting": f"{v.blood_glucose_fasting} mg/dL" if v.blood_glucose_fasting else "N/A",
                "hba1c": f"{v.hba1c} %" if v.hba1c else "N/A",
                "weight_kg": f"{v.weight_kg} kg" if v.weight_kg else "N/A",
                "spo2": f"{v.oxygen_saturation_spo2} %" if v.oxygen_saturation_spo2 else "N/A",
                "notes": v.notes or ""
            }
            for v in vitals
        ]

        # 5. Generate Grounded Discussion Questions
        questions = []
        
        # Questions based on abnormal lab flags or significant changes
        for m in lab_measurements_data:
            if m["flag"] in [LabFlag.HIGH.value, LabFlag.LOW.value, LabFlag.CRITICAL.value, LabFlag.ABNORMAL.value]:
                questions.append(
                    f"My {m['test_name']} was recorded at {m['latest_value']} (Status: {m['flag'].upper()}) on {m['date']}. What follow-up steps or lifestyle adjustments are recommended?"
                )
            elif m["trend_direction"] in ["Increased", "Decreased"]:
                questions.append(
                    f"My {m['test_name']} showed a change from {m['previous_value']} to {m['latest_value']} ({m['percentage_change']}). Could you help me interpret this change?"
                )

        # Questions based on active prescriptions
        for rx in prescriptions_data[:2]:
            questions.append(
                f"For {rx['medication_name']} ({rx['dosage']}), are there any specific food interactions or timing guidelines I should follow?"
            )

        # Baseline fallback question if records exist but no abnormalities
        if (lab_measurements_data or prescriptions_data or recent_docs_data) and not questions:
            questions.append("Based on my recent laboratory and health records, are any routine screenings or preventive checkups recommended at this time?")

        # 6. Gather Evidence Sources & Provenance
        sources_map = {}
        for m in lab_measurements_data:
            if m.get("document_id") and m.get("source_document"):
                sources_map[m["document_id"]] = {
                    "source_name": m["source_document"],
                    "document_id": m["document_id"],
                    "page_number": m.get("page_number", 1),
                    "source_type": "USER_STRUCTURED_RECORD",
                    "text_snippet": f"Lab Test: {m['test_name']} = {m['latest_value']} ({m['date']})"
                }
        for rx in prescriptions_data:
            if rx.get("document_id") and rx.get("source_document") and rx["document_id"] not in sources_map:
                sources_map[rx["document_id"]] = {
                    "source_name": rx["source_document"],
                    "document_id": rx["document_id"],
                    "page_number": rx.get("page_number", 1),
                    "source_type": "USER_STRUCTURED_RECORD",
                    "text_snippet": f"Prescription: {rx['medication_name']} {rx['dosage']} by {rx['doctor_name']}"
                }
        for d in recent_docs_data:
            if d["id"] not in sources_map:
                sources_map[d["id"]] = {
                    "source_name": d["title"],
                    "document_id": d["id"],
                    "page_number": 1,
                    "source_type": "USER_DOCUMENT",
                    "text_snippet": f"Uploaded Document: {d['title']} ({d['category']})"
                }

        sources_data = list(sources_map.values())

        # Compile structured summary payload
        summary_payload = {
            "patient_info": {
                "full_name": user.full_name if user else "Patient",
                "email": user.email if user else "",
                "date_of_birth": user.date_of_birth or "Not specified",
                "gender": user.gender or "Not specified",
                "blood_group": user.blood_group or "Not specified"
            },
            "generation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "recent_documents": recent_docs_data,
            "lab_measurements": lab_measurements_data,
            "prescriptions": prescriptions_data,
            "vital_records": vitals_data,
            "health_trends": health_trends_data,
            "generated_questions": questions,
            "sources": sources_data,
            "excluded_sections": [],
            "custom_notes": "",
            "disclaimer": self.DISCLAIMER_TEXT
        }

        title = req.title.strip() if req.title and req.title.strip() else "General Medical Consultation Summary"

        summary_record = AppointmentSummary(
            user_id=user_id,
            title=title,
            date_range_start=req.date_range_start,
            date_range_end=req.date_range_end,
            summary_data=summary_payload
        )
        db.add(summary_record)
        db.commit()
        db.refresh(summary_record)

        return summary_record

    def update_summary(
        self,
        db: Session,
        user_id: int,
        summary_id: int,
        update_req: AppointmentSummaryUpdateRequest
    ) -> Optional[AppointmentSummary]:
        """
        Updates the AppointmentSummary artifact without modifying underlying medical records.
        """
        summary = db.query(AppointmentSummary).filter(
            AppointmentSummary.id == summary_id,
            AppointmentSummary.user_id == user_id
        ).first()

        if not summary:
            return None

        data = dict(summary.summary_data)

        if update_req.title is not None:
            summary.title = update_req.title.strip()
        if update_req.generated_questions is not None:
            data["generated_questions"] = update_req.generated_questions
        if update_req.excluded_sections is not None:
            data["excluded_sections"] = update_req.excluded_sections
        if update_req.custom_notes is not None:
            data["custom_notes"] = update_req.custom_notes
        if update_req.summary_data is not None:
            # Merge custom user adjustments while preserving patient info & disclaimer
            for k, v in update_req.summary_data.items():
                if k in ["lab_measurements", "prescriptions", "recent_documents", "vital_records", "health_trends", "sources", "generated_questions", "excluded_sections", "custom_notes"]:
                    data[k] = v

        summary.summary_data = data
        summary.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(summary)
        return summary

    def generate_pdf(self, summary: AppointmentSummary, user: User) -> io.BytesIO:
        """
        Renders a clean, professional, publication-quality medical summary PDF using ReportLab.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        # Custom typography & styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0891b2'),
            textTransform='uppercase',
            spaceAfter=10
        )
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=10,
            spaceAfter=5
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#334155')
        )
        body_bold = ParagraphStyle(
            'BodyBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        flag_high = ParagraphStyle(
            'FlagHigh',
            parent=body_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#b91c1c')
        )
        flag_normal = ParagraphStyle(
            'FlagNormal',
            parent=body_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#15803d')
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#64748b')
        )

        data = summary.summary_data or {}
        excluded = set(data.get("excluded_sections", []))

        elements = []

        # 1. Header Banner
        header_text = Paragraph("HEALTHMATE AI — CLINICAL PREPARATION SUMMARY", subtitle_style)
        main_title = Paragraph(summary.title or "General Medical Consultation Summary", title_style)
        elements.append(header_text)
        elements.append(main_title)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0891b2'), spaceBefore=2, spaceAfter=8))

        # 2. Patient Demographics & Summary Info Table
        patient_info = data.get("patient_info", {})
        gen_date = data.get("generation_date", datetime.now().strftime("%Y-%m-%d"))
        
        patient_table_data = [
            [
                Paragraph(f"<b>Patient Name:</b> {patient_info.get('full_name', user.full_name or 'Patient')}", body_style),
                Paragraph(f"<b>Date of Birth:</b> {patient_info.get('date_of_birth', user.date_of_birth or 'N/A')}", body_style),
                Paragraph(f"<b>Gender:</b> {patient_info.get('gender', user.gender or 'N/A')}", body_style),
            ],
            [
                Paragraph(f"<b>Blood Group:</b> {patient_info.get('blood_group', user.blood_group or 'N/A')}", body_style),
                Paragraph(f"<b>Generation Date:</b> {gen_date}", body_style),
                Paragraph(f"<b>Security Isolation:</b> User Verified (Vault #{user.id})", body_style),
            ]
        ]
        patient_table = Table(patient_table_data, colWidths=[180, 180, 180])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(patient_table)
        elements.append(Spacer(1, 10))

        # 3. Section: Recent Medical Records & Reports
        if "documents" not in excluded and data.get("recent_documents"):
            elements.append(Paragraph("1. Recent Medical Documents & Diagnostic Reports", section_title_style))
            doc_rows = [[
                Paragraph("<b>Document Title / Name</b>", body_bold),
                Paragraph("<b>Category</b>", body_bold),
                Paragraph("<b>Report Date</b>", body_bold),
                Paragraph("<b>Uploaded Date</b>", body_bold),
            ]]
            for d in data.get("recent_documents", []):
                doc_rows.append([
                    Paragraph(d.get("title", "Untitled"), body_style),
                    Paragraph(d.get("category", "General"), body_style),
                    Paragraph(d.get("document_date", "Undated"), body_style),
                    Paragraph(d.get("created_at", "Undated"), body_style),
                ])
            t_docs = Table(doc_rows, colWidths=[200, 110, 110, 120])
            t_docs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
                ('PADDING', (0, 0), (-1, -1), 3.5),
            ]))
            elements.append(t_docs)
            elements.append(Spacer(1, 10))

        # 4. Section: Health Measurements & Trends
        if "lab_measurements" not in excluded and data.get("lab_measurements"):
            elements.append(Paragraph("2. Health Measurements & Trend Changes", section_title_style))
            meas_rows = [[
                Paragraph("<b>Test Name</b>", body_bold),
                Paragraph("<b>Latest Value</b>", body_bold),
                Paragraph("<b>Previous Value</b>", body_bold),
                Paragraph("<b>Change (%)</b>", body_bold),
                Paragraph("<b>Ref. Range</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
            ]]
            for m in data.get("lab_measurements", []):
                flag = m.get("flag", "normal").lower()
                flag_p = Paragraph(m.get("flag", "NORMAL").upper(), flag_high if flag in ['high', 'critical', 'abnormal', 'low'] else flag_normal)
                change_display = f"{m.get('change', 'N/A')} ({m.get('percentage_change', '')})" if m.get('percentage_change') not in ['N/A', 'Not available'] else m.get('change', 'N/A')
                meas_rows.append([
                    Paragraph(m.get("test_name", "Test"), body_style),
                    Paragraph(f"{m.get('latest_value', 'N/A')} ({m.get('date', '')})", body_style),
                    Paragraph(f"{m.get('previous_value', 'N/A')}", body_style),
                    Paragraph(change_display, body_style),
                    Paragraph(m.get("reference_range", "N/A"), body_style),
                    flag_p
                ])
            t_meas = Table(meas_rows, colWidths=[110, 115, 95, 95, 75, 50])
            t_meas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
                ('PADDING', (0, 0), (-1, -1), 3.5),
            ]))
            elements.append(t_meas)
            elements.append(Spacer(1, 10))

        # 5. Section: Active Prescription Medications
        if "prescriptions" not in excluded and data.get("prescriptions"):
            elements.append(Paragraph("3. Active Prescription Medications", section_title_style))
            rx_rows = [[
                Paragraph("<b>Medication</b>", body_bold),
                Paragraph("<b>Dosage</b>", body_bold),
                Paragraph("<b>Frequency & Timing</b>", body_bold),
                Paragraph("<b>Duration</b>", body_bold),
                Paragraph("<b>Prescriber</b>", body_bold),
            ]]
            for rx in data.get("prescriptions", []):
                freq_timing = f"{rx.get('frequency', '')} — {rx.get('timing_instructions', '')}".strip(" —")
                rx_rows.append([
                    Paragraph(rx.get("medication_name", "Medicine"), body_style),
                    Paragraph(rx.get("dosage", "Standard"), body_style),
                    Paragraph(freq_timing or "As directed", body_style),
                    Paragraph(rx.get("duration", "Ongoing"), body_style),
                    Paragraph(rx.get("doctor_name", "Physician"), body_style),
                ])
            t_rx = Table(rx_rows, colWidths=[130, 80, 170, 75, 85])
            t_rx.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
                ('PADDING', (0, 0), (-1, -1), 3.5),
            ]))
            elements.append(t_rx)
            elements.append(Spacer(1, 10))

        # 6. Section: Vital Signs
        if "vitals" not in excluded and data.get("vital_records"):
            elements.append(Paragraph("4. Recent Vital Signs", section_title_style))
            vit_rows = [[
                Paragraph("<b>Date</b>", body_bold),
                Paragraph("<b>Blood Pressure</b>", body_bold),
                Paragraph("<b>Heart Rate</b>", body_bold),
                Paragraph("<b>Blood Glucose</b>", body_bold),
                Paragraph("<b>SpO2</b>", body_bold),
                Paragraph("<b>Weight / BMI</b>", body_bold),
            ]]
            for v in data.get("vital_records", []):
                vit_rows.append([
                    Paragraph(v.get("record_date", "Undated"), body_style),
                    Paragraph(v.get("bp", "N/A"), body_style),
                    Paragraph(v.get("heart_rate", "N/A"), body_style),
                    Paragraph(v.get("glucose_fasting", "N/A"), body_style),
                    Paragraph(v.get("spo2", "N/A"), body_style),
                    Paragraph(f"{v.get('weight_kg', 'N/A')}", body_style),
                ])
            t_vit = Table(vit_rows, colWidths=[90, 100, 80, 90, 70, 110])
            t_vit.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
                ('PADDING', (0, 0), (-1, -1), 3.5),
            ]))
            elements.append(t_vit)
            elements.append(Spacer(1, 10))

        # 7. Section: Key Changes & Clinical Observations
        if "trends" not in excluded and data.get("health_trends"):
            elements.append(Paragraph("5. Notable Recorded Changes (Health Intelligence)", section_title_style))
            trend_items = []
            for tr in data.get("health_trends", []):
                trend_items.append([
                    Paragraph(f"• <b>{tr.get('test_name', '')}</b>: {tr.get('observation', '')} <i>[Source: {tr.get('source_document', '')}]</i>", body_style)
                ])
            t_tr = Table(trend_items, colWidths=[540])
            t_tr.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_tr)
            elements.append(Spacer(1, 10))

        # 8. Section: Questions to Discuss with Healthcare Professional
        if "questions" not in excluded and data.get("generated_questions"):
            elements.append(Paragraph("6. Suggested Questions to Discuss with Your Doctor", section_title_style))
            q_items = []
            for i, q in enumerate(data.get("generated_questions", []), 1):
                q_items.append([
                    Paragraph(f"<b>Q{i}.</b> {q}", body_style)
                ])
            t_q = Table(q_items, colWidths=[540])
            t_q.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#86efac')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dcfce7')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_q)
            elements.append(Spacer(1, 10))

        # 9. Section: Evidence Sources & Provenance
        if "sources" not in excluded and data.get("sources"):
            elements.append(Paragraph("7. Verified Evidence Sources & Provenance", section_title_style))
            src_rows = [[
                Paragraph("<b>Source Document</b>", body_bold),
                Paragraph("<b>Page #</b>", body_bold),
                Paragraph("<b>Extracted Evidence / Excerpt</b>", body_bold),
            ]]
            for s in data.get("sources", []):
                src_rows.append([
                    Paragraph(s.get("source_name", "Uploaded File"), body_style),
                    Paragraph(str(s.get("page_number", 1)), body_style),
                    Paragraph(s.get("text_snippet", "")[:140], body_style),
                ])
            t_src = Table(src_rows, colWidths=[160, 50, 330])
            t_src.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
                ('PADDING', (0, 0), (-1, -1), 3.5),
            ]))
            elements.append(t_src)
            elements.append(Spacer(1, 10))

        # 10. Clinical Disclaimer
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#94a3b8'), spaceBefore=4, spaceAfter=6))
        elements.append(Paragraph(f"<b>Clinical Safety Disclaimer:</b> {self.DISCLAIMER_TEXT}", disclaimer_style))

        # Build PDF with Page X of Y canvas
        doc.build(elements, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer

appointment_summary_service = AppointmentSummaryService()
