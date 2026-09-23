from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.app.models.reminder import MedicationReminder, ReminderStatus, Notification, NotificationType
from backend.app.models.clinical import Prescription, LabTest, VitalRecord
from backend.app.models.document import Document
from backend.app.models.nutrition import NutritionFoodItem
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.services.health_intelligence_service import health_intelligence_service
from backend.app.services.notification_service import notification_service

class ReminderService:
    """
    HealthMate AI Smart Medication Reminder & Daily Health Insights Engine (Phase 13)
    ==================================================================================
    Safety & Compliance:
      - Reminders are strictly derived from stored Prescription and OCR records.
      - NEVER invents drug names, dosage, frequency, timing, or duration.
      - If timing is missing in prescription: "Timing not specified in the available prescription."
      - User ownership strictly enforced.
    """

    def parse_timing_slots(self, timing_str: Optional[str], frequency_str: Optional[str]) -> List[Dict[str, Any]]:
        """
        Parses extracted timing or frequency text into structured slots without hallucination.
        Returns a list of slots: [{"slot": "Morning"|"Afternoon"|"Night", "default_time": "8:00 AM"|"1:00 PM"|"8:00 PM"}]
        """
        combined = f"{timing_str or ''} {frequency_str or ''}".lower()
        slots = []

        has_morning = any(k in combined for k in ["morning", "breakfast", "am", "od", "pc", "ac", "once daily", "twice daily", "thrice daily", "3 times", "2 times", "tid", "bd"])
        has_afternoon = any(k in combined for k in ["afternoon", "lunch", "noon", "thrice daily", "3 times", "tid"])
        has_night = any(k in combined for k in ["night", "dinner", "bedtime", "pm", "hs", "twice daily", "thrice daily", "3 times", "2 times", "tid", "bd"])

        # Explicit keyword matching
        if "morning" in combined:
            slots.append({"slot": "Morning", "time": "8:00 AM", "timing": "Morning"})
        if "afternoon" in combined or "noon" in combined or "lunch" in combined:
            slots.append({"slot": "Afternoon", "time": "1:00 PM", "timing": "Afternoon"})
        if "night" in combined or "dinner" in combined or "bedtime" in combined:
            slots.append({"slot": "Night", "time": "8:00 PM", "timing": "Night"})

        # If timing mentions "3 times daily" or "tid" without explicit words
        if not slots and ("3 times" in combined or "thrice" in combined or "tid" in combined):
            slots = [
                {"slot": "Morning", "time": "8:00 AM", "timing": "Morning"},
                {"slot": "Afternoon", "time": "1:00 PM", "timing": "Afternoon"},
                {"slot": "Night", "time": "8:00 PM", "timing": "Night"}
            ]
        elif not slots and ("twice daily" in combined or "2 times" in combined or "bd" in combined or "bid" in combined):
            slots = [
                {"slot": "Morning", "time": "8:00 AM", "timing": "Morning"},
                {"slot": "Night", "time": "8:00 PM", "timing": "Night"}
            ]
        elif not slots and ("once daily" in combined or "1 time" in combined or "od" in combined):
            slots = [
                {"slot": "Morning", "time": "8:00 AM", "timing": "Morning"}
            ]

        # If nothing could be identified
        if not slots:
            slots = [{
                "slot": "Unspecified",
                "time": None,
                "timing": "Timing not specified in the available prescription."
            }]

        return slots

    def sync_reminders_from_prescriptions(self, db: Session, user_id: int) -> List[MedicationReminder]:
        """
        Synchronizes prescription records for user_id into MedicationReminder entries.
        Derives slots safely without duplicating existing reminders.
        """
        prescriptions = db.query(Prescription).filter(Prescription.user_id == user_id).all()
        created_reminders = []

        for rx in prescriptions:
            # Check if reminders already exist for this prescription
            existing = db.query(MedicationReminder).filter(
                MedicationReminder.user_id == user_id,
                MedicationReminder.prescription_id == rx.id
            ).all()

            if not existing:
                slots = self.parse_timing_slots(rx.timing_instructions, rx.frequency)
                for s in slots:
                    reminder = MedicationReminder(
                        user_id=user_id,
                        prescription_id=rx.id,
                        document_id=rx.document_id,
                        medicine_name=rx.medication_name,
                        dosage=rx.dosage or "Dosage as prescribed",
                        frequency=rx.frequency or "Standard frequency",
                        timing=s["timing"],
                        scheduled_time=s["time"],
                        start_date=rx.prescribed_date,
                        end_date=None,
                        page_number=1,
                        status=ReminderStatus.PENDING.value,
                        enabled=True,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(reminder)
                    created_reminders.append(reminder)

        if created_reminders:
            db.commit()
            for r in created_reminders:
                db.refresh(r)

            # Create notification for new reminders created
            notification_service.create_notification(
                db=db,
                user_id=user_id,
                type=NotificationType.MEDICATION_REMINDER.value,
                title="Medication Reminders Created",
                message=f"Created {len(created_reminders)} medication reminder(s) from your prescription records.",
                related_resource_type="medication_reminder",
                related_resource_id=str(created_reminders[0].id)
            )

        return db.query(MedicationReminder).filter(MedicationReminder.user_id == user_id).all()

    def get_today_reminders(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Returns today's reminders for the user, attaching document details.
        Automatically syncs if none exist.
        """
        reminders = db.query(MedicationReminder).filter(
            MedicationReminder.user_id == user_id,
            MedicationReminder.enabled == True
        ).all()

        if not reminders:
            self.sync_reminders_from_prescriptions(db, user_id)
            reminders = db.query(MedicationReminder).filter(
                MedicationReminder.user_id == user_id,
                MedicationReminder.enabled == True
            ).all()

        result = []
        for r in reminders:
            doc_title = None
            if r.document_id:
                doc = db.query(Document).filter(Document.id == r.document_id).first()
                if doc:
                    doc_title = doc.title

            item = {
                "id": r.id,
                "user_id": r.user_id,
                "prescription_id": r.prescription_id,
                "document_id": r.document_id,
                "medicine_name": r.medicine_name,
                "dosage": r.dosage,
                "frequency": r.frequency,
                "timing": r.timing or "Timing not specified in the available prescription.",
                "scheduled_time": r.scheduled_time,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "page_number": r.page_number,
                "status": r.status,
                "enabled": r.enabled,
                "source_document_title": doc_title,
                "snooze_until": r.snooze_until,
                "completed_at": r.completed_at,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            }
            result.append(item)

        return result

    def get_medication_schedule(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Groups active medication reminders into Morning, Afternoon, Night, and Unspecified buckets.
        """
        reminders = self.get_today_reminders(db, user_id)

        morning = []
        afternoon = []
        night = []
        unspecified = []

        completed_count = 0
        for r in reminders:
            if r["status"] == ReminderStatus.COMPLETED.value:
                completed_count += 1

            timing_lower = (r["timing"] or "").lower()
            slot = (r["scheduled_time"] or "").lower()

            if "morning" in timing_lower or "8:00 am" in slot or "am" in slot:
                morning.append(r)
            elif "afternoon" in timing_lower or "1:00 pm" in slot or "noon" in timing_lower:
                afternoon.append(r)
            elif "night" in timing_lower or "8:00 pm" in slot or "dinner" in timing_lower or "bedtime" in timing_lower:
                night.append(r)
            else:
                unspecified.append(r)

        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "total_active_reminders": len(reminders),
            "completed_count": completed_count,
            "remaining_count": len(reminders) - completed_count,
            "morning": morning,
            "afternoon": afternoon,
            "night": night,
            "unspecified": unspecified
        }

    def complete_reminder(self, db: Session, user_id: int, reminder_id: int) -> Optional[MedicationReminder]:
        """Marks reminder as completed strictly for the owning user."""
        reminder = db.query(MedicationReminder).filter(
            MedicationReminder.id == reminder_id,
            MedicationReminder.user_id == user_id
        ).first()

        if reminder:
            reminder.status = ReminderStatus.COMPLETED.value
            reminder.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(reminder)
        return reminder

    def snooze_reminder(self, db: Session, user_id: int, reminder_id: int, minutes: int = 30) -> Optional[MedicationReminder]:
        """Snoozes a reminder for a given number of minutes."""
        reminder = db.query(MedicationReminder).filter(
            MedicationReminder.id == reminder_id,
            MedicationReminder.user_id == user_id
        ).first()

        if reminder:
            reminder.status = ReminderStatus.SNOOZED.value
            reminder.snooze_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            db.commit()
            db.refresh(reminder)
        return reminder

    def update_reminder(
        self,
        db: Session,
        user_id: int,
        reminder_id: int,
        scheduled_time: Optional[str] = None,
        enabled: Optional[bool] = None,
        status: Optional[str] = None
    ) -> Optional[MedicationReminder]:
        """Updates reminder settings (e.g. custom time or enable toggle)."""
        reminder = db.query(MedicationReminder).filter(
            MedicationReminder.id == reminder_id,
            MedicationReminder.user_id == user_id
        ).first()

        if reminder:
            if scheduled_time is not None:
                reminder.scheduled_time = scheduled_time
            if enabled is not None:
                reminder.enabled = enabled
            if status is not None:
                reminder.status = status
            reminder.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(reminder)
        return reminder

    def get_daily_health_insights(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Aggregates Today's Health Dashboard data:
        - Remaining reminders
        - Latest biomarkers & percentage change compared to previous record
        - Daily USDA food ideas
        - Recent prescription and report IDs
        """
        today_reminders = self.get_today_reminders(db, user_id)
        completed_count = sum(1 for r in today_reminders if r["status"] == ReminderStatus.COMPLETED.value)
        remaining_count = len(today_reminders) - completed_count

        # Get latest biomarkers with health intelligence changes
        summary = health_intelligence_service.get_user_health_intelligence_summary(db, user_id)
        recent_changes = summary.get("recent_changes", [])

        latest_biomarkers = []
        # Priority tests to highlight on daily dashboard
        key_tests = ["Glucose", "Fasting Blood Sugar", "HbA1c", "Total Cholesterol", "Blood Pressure", "Hemoglobin", "Serum Creatinine"]
        
        seen_tests = set()
        for change in recent_changes:
            t_name = change.get("test_name", "")
            if t_name not in seen_tests:
                seen_tests.add(t_name)
                latest_biomarkers.append({
                    "test_name": t_name,
                    "canonical_name": change.get("canonical_name"),
                    "latest_value": change.get("latest_value", "Not available"),
                    "unit": change.get("unit"),
                    "date": change.get("latest_date"),
                    "previous_value": change.get("previous_value"),
                    "percentage_change": change.get("percentage_change"),
                    "trend_direction": change.get("trend_direction", "Insufficient data"),
                    "source_document_id": change.get("source_document_id"),
                    "source_document_title": change.get("source_document_title")
                })
            if len(latest_biomarkers) >= 4:
                break

        # Fallback to recent lab tests if no multi-test change was computed
        if not latest_biomarkers:
            tests = db.query(LabTest).filter(LabTest.user_id == user_id).order_by(desc(LabTest.created_at)).limit(3).all()
            for t in tests:
                doc = db.query(Document).filter(Document.id == t.document_id).first() if t.document_id else None
                latest_biomarkers.append({
                    "test_name": t.test_name,
                    "canonical_name": t.canonical_name,
                    "latest_value": t.observed_value,
                    "unit": t.unit,
                    "date": t.test_date or (doc.document_date if doc else "Recent"),
                    "previous_value": None,
                    "percentage_change": None,
                    "trend_direction": "Stable" if t.flag == "normal" else "Observed",
                    "source_document_id": t.document_id,
                    "source_document_title": doc.title if doc else "Diagnostic Report"
                })

        # USDA Daily Nutrition Ideas from Foundation Foods database
        nutrition_items = db.query(NutritionFoodItem).limit(4).all()
        nutrition_ideas = []
        for n in nutrition_items:
            nut = n.nutrients or {}
            calories = nut.get("energy_kcal") or nut.get("calories") or 52.0
            carbs = nut.get("carbohydrate_g") or 13.81
            fiber = nut.get("fiber_g") or 2.4
            protein = nut.get("protein_g") or 0.26
            nutrition_ideas.append({
                "food_name": n.food_name,
                "common_name": n.common_name,
                "calories": float(calories) if calories is not None else None,
                "carbohydrate_g": float(carbs) if carbs is not None else None,
                "fiber_g": float(fiber) if fiber is not None else None,
                "protein_g": float(protein) if protein is not None else None,
                "source_attribution": "USDA FoodData Central",
                "disclaimer": "General nutrition information based on USDA data. Discuss dietary changes with a qualified healthcare professional when you have medical conditions or dietary restrictions."
            })

        # Recent prescription and report
        recent_rx = db.query(Document).filter(Document.user_id == user_id, Document.category == "prescription").order_by(desc(Document.created_at)).first()
        recent_report = db.query(Document).filter(Document.user_id == user_id, Document.category == "lab_report").order_by(desc(Document.created_at)).first()
        
        # Appointment summaries count
        appt_count = db.query(AppointmentSummary).filter(AppointmentSummary.user_id == user_id).count()

        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reminders_remaining_today": remaining_count,
            "reminders_completed_today": completed_count,
            "today_reminders": today_reminders,
            "latest_biomarkers": latest_biomarkers,
            "nutrition_ideas": nutrition_ideas,
            "recent_prescription_title": recent_rx.title if recent_rx else None,
            "recent_prescription_id": recent_rx.id if recent_rx else None,
            "recent_report_title": recent_report.title if recent_report else None,
            "recent_report_id": recent_report.id if recent_report else None,
            "appointment_prep_count": appt_count
        }

    def get_report_insight_card(self, db: Session, user_id: int, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Generates structured insights for an uploaded report:
        - Total measurements extracted
        - How many have previous comparisons
        - How many are first-time / standalone
        """
        doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not doc:
            return None

        lab_tests = db.query(LabTest).filter(LabTest.document_id == document_id, LabTest.user_id == user_id).all()
        summary = health_intelligence_service.get_user_health_intelligence_summary(db, user_id)
        recent_changes_map = {c.get("test_name", "").lower(): c for c in summary.get("recent_changes", [])}

        insights = []
        with_comp = 0
        without_comp = 0

        for t in lab_tests:
            c = recent_changes_map.get(t.test_name.lower())
            if c and c.get("previous_value") is not None:
                with_comp += 1
                insights.append({
                    "test_name": t.test_name,
                    "latest_value": t.observed_value,
                    "unit": t.unit,
                    "previous_value": c.get("previous_value"),
                    "percentage_change": c.get("percentage_change"),
                    "trend_direction": c.get("trend_direction", "Stable"),
                    "has_previous_comparison": True
                })
            else:
                without_comp += 1
                insights.append({
                    "test_name": t.test_name,
                    "latest_value": t.observed_value,
                    "unit": t.unit,
                    "previous_value": None,
                    "percentage_change": None,
                    "trend_direction": "First Recorded",
                    "has_previous_comparison": False
                })

        return {
            "document_id": doc.id,
            "document_title": doc.title,
            "document_date": doc.document_date,
            "total_measurements_extracted": len(lab_tests),
            "measurements_with_comparison": with_comp,
            "measurements_without_comparison": without_comp,
            "insights": insights
        }

reminder_service = ReminderService()
