import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import Prescription, LabTest, LabFlag
from backend.app.models.reminder import MedicationReminder, Notification, ReminderStatus, NotificationType
from backend.app.models.nutrition import NutritionFoodItem
from backend.app.models.audit import AuditLog
from backend.app.services.reminder_service import reminder_service
from backend.app.services.notification_service import notification_service

def test_1_reminder_creation_and_sync_from_prescriptions(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # 1. Create a prescription document and prescription record
    doc = Document(
        user_id=user_id,
        original_filename="Amox_Prescription.pdf",
        stored_filename="amox_1.pdf",
        file_path="uploads/amox_1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_amox_1",
        category=DocumentCategory.PRESCRIPTION.value,
        title="Doctor Prescription - March",
        document_date="2026-03-20"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    rx = Prescription(
        document_id=doc.id,
        user_id=user_id,
        medication_name="Amoxicillin",
        dosage="500 mg",
        frequency="3 times daily",
        timing_instructions="Morning / Afternoon / Night",
        duration="5 days",
        prescribed_date="2026-03-20"
    )
    db_session.add(rx)
    db_session.commit()

    # 2. Call sync endpoint
    sync_resp = client.post("/api/v1/reminders/sync", headers=headers)
    assert sync_resp.status_code == 200
    reminders = sync_resp.json()
    assert len(reminders) >= 3

    # Verify slots
    timings = [r["timing"] for r in reminders]
    assert "Morning" in timings
    assert "Afternoon" in timings
    assert "Night" in timings

    for r in reminders:
        assert r["medicine_name"] == "Amoxicillin"
        assert r["dosage"] == "500 mg"
        assert r["source_document_title"] == "Doctor Prescription - March"
        assert r["document_id"] == doc.id


def test_2_cross_user_reminder_isolation(client: TestClient, registered_user: dict, db_session: Session):
    user_a_id = registered_user["user"]["id"]
    
    # Register User B
    reg_b = client.post("/api/v1/auth/register", json={
        "email": "user_b_reminders@example.com",
        "password": "Password123!",
        "full_name": "User B",
        "role": "patient"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create reminder for User A
    rem_a = MedicationReminder(
        user_id=user_a_id,
        medicine_name="Metformin",
        dosage="500 mg",
        timing="Morning",
        scheduled_time="8:00 AM",
        status=ReminderStatus.PENDING.value,
        enabled=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(rem_a)
    db_session.commit()
    db_session.refresh(rem_a)

    # User B should not see User A's reminder
    resp_b = client.get("/api/v1/reminders/today", headers=headers_b)
    assert resp_b.status_code == 200
    b_reminders = resp_b.json()
    assert not any(r["id"] == rem_a.id for r in b_reminders)

    # User B cannot complete User A's reminder
    complete_resp = client.post(f"/api/v1/reminders/{rem_a.id}/complete", headers=headers_b)
    assert complete_resp.status_code == 404

    # User B cannot snooze User A's reminder
    snooze_resp = client.post(f"/api/v1/reminders/{rem_a.id}/snooze", json={"snooze_minutes": 30}, headers=headers_b)
    assert snooze_resp.status_code == 404


def test_3_missing_timing_and_dosage_handling(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Prescription without timing or dosage
    rx = Prescription(
        user_id=user_id,
        medication_name="Paracetamol",
        dosage=None,
        frequency=None,
        timing_instructions=None,
        duration=None
    )
    db_session.add(rx)
    db_session.commit()

    sync_resp = client.post("/api/v1/reminders/sync", headers=headers)
    assert sync_resp.status_code == 200
    reminders = sync_resp.json()

    paracetamol_rems = [r for r in reminders if r["medicine_name"] == "Paracetamol"]
    assert len(paracetamol_rems) == 1
    assert "Timing not specified in the available prescription." in paracetamol_rems[0]["timing"]
    assert paracetamol_rems[0]["scheduled_time"] is None


def test_4_reminder_lifecycle_complete_and_snooze(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    rem = MedicationReminder(
        user_id=user_id,
        medicine_name="Atorvastatin",
        dosage="20 mg",
        timing="Night",
        scheduled_time="8:00 PM",
        status=ReminderStatus.PENDING.value,
        enabled=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(rem)
    db_session.commit()
    db_session.refresh(rem)

    # 1. Snooze
    snooze_resp = client.post(f"/api/v1/reminders/{rem.id}/snooze", json={"snooze_minutes": 45}, headers=headers)
    assert snooze_resp.status_code == 200
    data = snooze_resp.json()
    assert data["status"] == "SNOOZED"
    assert data["snooze_until"] is not None

    # 2. Complete
    comp_resp = client.post(f"/api/v1/reminders/{rem.id}/complete", headers=headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["completed_at"] is not None

    # 3. Update settings
    upd_resp = client.put(f"/api/v1/reminders/{rem.id}", json={"scheduled_time": "9:00 PM", "enabled": True}, headers=headers)
    assert upd_resp.status_code == 200
    assert upd_resp.json()["scheduled_time"] == "9:00 PM"


def test_5_notification_creation_and_isolation(client: TestClient, registered_user: dict, db_session: Session):
    user_a_id = registered_user["user"]["id"]
    headers_a = registered_user["headers"]

    # Register User B
    reg_b = client.post("/api/v1/auth/register", json={
        "email": "user_b_notifs@example.com",
        "password": "Password123!",
        "full_name": "User B Notifications",
        "role": "patient"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create notification for User A
    notif_a = notification_service.create_notification(
        db=db_session,
        user_id=user_a_id,
        type=NotificationType.MEDICATION_REMINDER.value,
        title="Morning Medication Due",
        message="Time to take Amoxicillin 500 mg."
    )

    # User A views notifications
    resp_a = client.get("/api/v1/notifications", headers=headers_a)
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert data_a["unread_count"] >= 1
    assert any(n["id"] == notif_a.id for n in data_a["notifications"])

    # User B should NOT see User A's notification
    resp_b = client.get("/api/v1/notifications", headers=headers_b)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert not any(n["id"] == notif_a.id for n in data_b["notifications"])

    # User B cannot mark User A's notification as read
    read_resp_b = client.post(f"/api/v1/notifications/{notif_a.id}/read", headers=headers_b)
    assert read_resp_b.status_code == 404

    # User A marks as read
    read_resp_a = client.post(f"/api/v1/notifications/{notif_a.id}/read", headers=headers_a)
    assert read_resp_a.status_code == 200
    assert read_resp_a.json()["is_read"] is True

    # User A marks all as read
    mark_all_resp = client.post("/api/v1/notifications/read-all", headers=headers_a)
    assert mark_all_resp.status_code == 200


def test_6_daily_health_dashboard_and_nutrition(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Ensure a USDA food item exists
    food = db_session.query(NutritionFoodItem).first()
    if not food:
        food = NutritionFoodItem(
            fdc_id=1102578,
            food_name="Apples, raw, with skin",
            common_name="Apple",
            food_category="Fruits and Fruit Juices",
            serving_size=100.0,
            serving_unit="g",
            nutrients={
                "energy_kcal": 52.0,
                "carbohydrate_g": 13.81,
                "fiber_g": 2.4,
                "protein_g": 0.26
            }
        )
        db_session.add(food)
        db_session.commit()

    # Create a lab test record
    lab = LabTest(
        user_id=user_id,
        test_name="Glucose",
        canonical_name="glucose_fasting",
        observed_value="105",
        numeric_value=105.0,
        unit="mg/dL",
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-20"
    )
    db_session.add(lab)
    db_session.commit()

    # Call daily-insights endpoint
    resp = client.get("/api/v1/reminders/daily-insights", headers=headers)
    assert resp.status_code == 200
    insights = resp.json()

    assert "reminders_remaining_today" in insights
    assert "latest_biomarkers" in insights
    assert len(insights["latest_biomarkers"]) >= 1
    assert "105" in insights["latest_biomarkers"][0]["latest_value"]

    assert "nutrition_ideas" in insights
    assert len(insights["nutrition_ideas"]) >= 1
    assert "USDA FoodData Central" in insights["nutrition_ideas"][0]["source_attribution"]
    assert "Discuss dietary changes with a qualified healthcare professional" in insights["nutrition_ideas"][0]["disclaimer"]


def test_7_report_insight_card_generation(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Create document
    doc = Document(
        user_id=user_id,
        original_filename="Blood_Report_March.pdf",
        stored_filename="blood_rep_1.pdf",
        file_path="uploads/blood_rep_1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_blood_rep_1",
        category=DocumentCategory.LAB_REPORT.value,
        title="Comprehensive Blood Test",
        document_date="2026-03-20"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # Add 2 lab tests for this document
    lab1 = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Glucose",
        canonical_name="glucose",
        observed_value="105",
        numeric_value=105.0,
        unit="mg/dL",
        flag=LabFlag.NORMAL.value
    )
    lab2 = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Hemoglobin",
        canonical_name="hemoglobin",
        observed_value="13.5",
        numeric_value=13.5,
        unit="g/dL",
        flag=LabFlag.NORMAL.value
    )
    db_session.add_all([lab1, lab2])
    db_session.commit()

    resp = client.get(f"/api/v1/reminders/report-insights/{doc.id}", headers=headers)
    assert resp.status_code == 200
    card = resp.json()
    assert card["document_id"] == doc.id
    assert card["total_measurements_extracted"] == 2
    assert len(card["insights"]) == 2


def test_8_audit_logging_for_phase13_events(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Trigger create reminder
    rem_resp = client.post("/api/v1/reminders/create", json={
        "medicine_name": "Levothyroxine",
        "dosage": "50 mcg",
        "frequency": "Once daily",
        "timing": "Morning",
        "scheduled_time": "7:00 AM",
        "enabled": True,
        "page_number": 1
    }, headers=headers)
    assert rem_resp.status_code == 200
    rem_id = rem_resp.json()["id"]

    # Verify audit log
    log = db_session.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.action == "MEDICATION_REMINDER_CREATED"
    ).first()
    assert log is not None
    assert str(rem_id) in log.resource_id


def test_9_ai_assistant_multilingual_preservation_and_evidence_guard(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Ask in Tamil
    ta_resp = client.post("/api/v1/assistant/chat", json={
        "query": "What is in my report?",
        "language": "ta"
    }, headers=headers)
    assert ta_resp.status_code == 200
    ta_data = ta_resp.json()
    assert ta_data["language"] == "ta"

    # Ask in Tanglish
    tanglish_resp = client.post("/api/v1/assistant/chat", json={
        "query": "What is in my report?",
        "language": "tanglish"
    }, headers=headers)
    assert tanglish_resp.status_code == 200
    tanglish_data = tanglish_resp.json()
    assert tanglish_data["language"] == "tanglish"
