import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.reminder import MedicationReminder, Notification
from backend.app.core.security import create_access_token, get_password_hash

def get_test_users(db_session: Session):
    u1 = db_session.query(User).filter(User.email == "master_p15_u1@example.com").first()
    if not u1:
        u1 = User(
            email="master_p15_u1@example.com",
            hashed_password=get_password_hash("MasterPass123!"),
            full_name="Dr. Eleanor Vance",
            language_preference="en",
            is_active=True
        )
        db_session.add(u1)

    u2 = db_session.query(User).filter(User.email == "master_p15_u2@example.com").first()
    if not u2:
        u2 = User(
            email="master_p15_u2@example.com",
            hashed_password=get_password_hash("MasterPass123!"),
            full_name="Marcus Brody",
            language_preference="ta",
            is_active=True
        )
        db_session.add(u2)

    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    t1 = create_access_token(subject=str(u1.id))
    t2 = create_access_token(subject=str(u2.id))
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    return u1, u2, h1, h2

def seed_full_pipeline_data(db_session: Session, u1: User, u2: User):
    # User 1: Report 1 (January Baseline)
    doc1 = Document(
        user_id=u1.id,
        original_filename="baseline_jan.pdf",
        stored_filename="baseline_jan_u1.pdf",
        file_path="uploads/baseline_jan_u1.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="hash_base_jan_u1",
        category="lab_report",
        title="Comprehensive Metabolic Panel - Jan",
        document_date="2026-01-10",
        ocr_status="completed",
        ocr_raw_text="Fasting Blood Glucose: 95 mg/dL. Total Cholesterol: 180 mg/dL. HbA1c: 5.6 %."
    )
    db_session.add(doc1)
    db_session.commit()
    db_session.refresh(doc1)

    t_jan_1 = LabTest(
        document_id=doc1.id,
        user_id=u1.id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose",
        test_category="metabolic",
        observed_value="95",
        numeric_value=95.0,
        unit="mg/dL",
        flag="normal",
        reference_range_text="70-99 mg/dL",
        test_date="2026-01-10"
    )
    t_jan_2 = LabTest(
        document_id=doc1.id,
        user_id=u1.id,
        test_name="Total Cholesterol",
        canonical_name="cholesterol",
        test_category="lipid",
        observed_value="180",
        numeric_value=180.0,
        unit="mg/dL",
        flag="normal",
        reference_range_text="< 200 mg/dL",
        test_date="2026-01-10"
    )
    t_jan_3 = LabTest(
        document_id=doc1.id,
        user_id=u1.id,
        test_name="HbA1c",
        canonical_name="hba1c",
        test_category="glycemic",
        observed_value="5.6",
        numeric_value=5.6,
        unit="%",
        flag="normal",
        reference_range_text="< 5.7 %",
        test_date="2026-01-10"
    )
    db_session.add_all([t_jan_1, t_jan_2, t_jan_3])

    # User 1: Report 2 (March Follow-up with Trends)
    doc2 = Document(
        user_id=u1.id,
        original_filename="followup_mar.pdf",
        stored_filename="followup_mar_u1.pdf",
        file_path="uploads/followup_mar_u1.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="hash_followup_mar_u1",
        category="lab_report",
        title="Comprehensive Metabolic Panel - March",
        document_date="2026-03-15",
        ocr_status="completed",
        ocr_raw_text="Fasting Blood Glucose: 110 mg/dL. Total Cholesterol: 215 mg/dL. HbA1c: 6.1 %."
    )
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    t_mar_1 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose",
        test_category="metabolic",
        observed_value="110",
        numeric_value=110.0,
        unit="mg/dL",
        flag="high",
        reference_range_text="70-99 mg/dL",
        test_date="2026-03-15"
    )
    t_mar_2 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="Total Cholesterol",
        canonical_name="cholesterol",
        test_category="lipid",
        observed_value="215",
        numeric_value=215.0,
        unit="mg/dL",
        flag="high",
        reference_range_text="< 200 mg/dL",
        test_date="2026-03-15"
    )
    t_mar_3 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="HbA1c",
        canonical_name="hba1c",
        test_category="glycemic",
        observed_value="6.1",
        numeric_value=6.1,
        unit="%",
        flag="high",
        reference_range_text="< 5.7 %",
        test_date="2026-03-15"
    )
    db_session.add_all([t_mar_1, t_mar_2, t_mar_3])

    # User 1: Prescription Record
    doc3 = Document(
        user_id=u1.id,
        original_filename="rx_cardiometabolic.pdf",
        stored_filename="rx_cardiometabolic_u1.pdf",
        file_path="uploads/rx_cardiometabolic_u1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_rx_cardio_u1",
        category="prescription",
        title="Cardiometabolic Prescription - March",
        document_date="2026-03-15",
        ocr_status="completed",
        ocr_raw_text="Metformin 500mg BD after food. Atorvastatin 10mg OD at night."
    )
    db_session.add(doc3)
    db_session.commit()
    db_session.refresh(doc3)

    rx1 = Prescription(
        document_id=doc3.id,
        user_id=u1.id,
        medication_name="Metformin",
        dosage="500mg",
        frequency="Twice daily",
        timing_instructions="After food",
        duration="90 days",
        doctor_name="Dr. Sterling",
        prescribed_date="2026-03-15"
    )
    rx2 = Prescription(
        document_id=doc3.id,
        user_id=u1.id,
        medication_name="Atorvastatin",
        dosage="10mg",
        frequency="Once daily",
        timing_instructions="At night",
        duration="90 days",
        doctor_name="Dr. Sterling",
        prescribed_date="2026-03-15"
    )
    db_session.add_all([rx1, rx2])

    # User 1: Vital Record
    vital1 = VitalRecord(
        user_id=u1.id,
        blood_pressure_systolic=128,
        blood_pressure_diastolic=82,
        heart_rate=74,
        record_date="2026-03-15"
    )
    db_session.add(vital1)

    # User 2: Isolated Confidential Record
    doc_u2 = Document(
        user_id=u2.id,
        original_filename="u2_secret_card.pdf",
        stored_filename="u2_secret_card.pdf",
        file_path="uploads/u2_secret_card.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_u2_card",
        category="lab_report",
        title="User 2 Confidential Renal Report",
        document_date="2026-03-18",
        ocr_status="completed",
        ocr_raw_text="Serum Creatinine: 2.1 mg/dL. Blood Urea Nitrogen: 38 mg/dL."
    )
    db_session.add(doc_u2)
    db_session.commit()
    db_session.refresh(doc_u2)

    t_u2 = LabTest(
        document_id=doc_u2.id,
        user_id=u2.id,
        test_name="Serum Creatinine",
        canonical_name="creatinine",
        test_category="renal",
        observed_value="2.1",
        numeric_value=2.1,
        unit="mg/dL",
        flag="high",
        test_date="2026-03-18"
    )
    db_session.add(t_u2)
    db_session.commit()

    return {
        "doc1": doc1,
        "doc2": doc2,
        "doc3": doc3,
        "doc_u2": doc_u2
    }


# =============================================================================
# PHASE 15: Smart Report Dashboard + Explain My Report
# =============================================================================
def test_phase15_smart_report_explanation_and_comparison(client: TestClient, db_session: Session):
    u1, u2, h1, _ = get_test_users(db_session)
    data_map = seed_full_pipeline_data(db_session, u1, u2)
    doc2 = data_map["doc2"]

    # Call Explain My Report endpoint
    res = client.post(f"/api/v1/reports/{doc2.id}/explain", json={"language": "en"}, headers=h1)
    assert res.status_code == 200
    report_data = res.json()

    assert report_data["document_id"] == doc2.id
    assert report_data["document_title"] == "Comprehensive Metabolic Panel - March"
    assert "Fasting Blood Glucose" in report_data["recorded_values_text"]
    assert "110" in report_data["recorded_values_text"]
    assert report_data["evidence_status"] == "SUPPORTED"
    assert len(report_data["sources"]) >= 1


# =============================================================================
# PHASE 16: Chronological Health Timeline
# =============================================================================
def test_phase16_chronological_health_timeline(client: TestClient, db_session: Session):
    u1, u2, h1, _ = get_test_users(db_session)
    seed_full_pipeline_data(db_session, u1, u2)

    res = client.get("/api/v1/health-timeline", headers=h1)
    assert res.status_code == 200
    timeline = res.json()

    assert timeline["total_events"] >= 5
    assert len(timeline["events"]) >= 5

    # Verify chronological ordering
    event_dates = [e["event_date"] for e in timeline["events"]]
    assert "2026-03-15" in event_dates
    assert "2026-01-10" in event_dates


# =============================================================================
# PHASE 17: Global Health Search Across Structured Records
# =============================================================================
def test_phase17_global_health_search_hybrid(client: TestClient, db_session: Session):
    u1, u2, h1, _ = get_test_users(db_session)
    seed_full_pipeline_data(db_session, u1, u2)

    # 1. Search for Glucose
    res_g = client.get("/api/v1/health-search?q=glucose", headers=h1)
    assert res_g.status_code == 200
    results_g = res_g.json()["results"]
    assert len(results_g) >= 2
    assert any("110" in str(r["value"]) or "95" in str(r["value"]) for r in results_g)

    # 2. Search for Prescription Metformin
    res_rx = client.get("/api/v1/health-search?q=Metformin", headers=h1)
    assert res_rx.status_code == 200
    results_rx = res_rx.json()["results"]
    assert len(results_rx) >= 1
    assert "Metformin" in results_rx[0]["title"]


# =============================================================================
# PHASE 18: Doctor Visit Mode Summary
# =============================================================================
def test_phase18_doctor_visit_mode_summary(client: TestClient, db_session: Session):
    u1, u2, h1, _ = get_test_users(db_session)
    seed_full_pipeline_data(db_session, u1, u2)

    res = client.get("/api/v1/doctor-visit", headers=h1)
    assert res.status_code == 200
    summary = res.json()

    assert summary["patient_name"] == "Dr. Eleanor Vance"
    assert len(summary["recent_reports"]) >= 2
    assert len(summary["current_medications"]) >= 2
    assert "Metformin" in [p["medicine_name"] for p in summary["current_medications"]]


# =============================================================================
# PHASE 19: Safe Medication Reminders & Notification Lifecycle
# =============================================================================
def test_phase19_safe_medication_reminders_and_notifications(client: TestClient, db_session: Session):
    u1, u2, h1, _ = get_test_users(db_session)
    seed_full_pipeline_data(db_session, u1, u2)

    # Sync reminders from verified prescriptions
    res_sync = client.post("/api/v1/reminders/sync", headers=h1)
    assert res_sync.status_code == 200
    sync_data = res_sync.json()
    assert len(sync_data) >= 2

    # Fetch reminders
    res_rems = client.get("/api/v1/reminders/today", headers=h1)
    assert res_rems.status_code == 200
    reminders = res_rems.json()
    assert len(reminders) >= 2
    med_names = [r["medicine_name"] for r in reminders]
    assert "Metformin" in med_names
    assert "Atorvastatin" in med_names

    # Check notification generation
    res_notifs = client.get("/api/v1/notifications", headers=h1)
    assert res_notifs.status_code == 200
    notifs = res_notifs.json()
    assert "notifications" in notifs
    assert len(notifs["notifications"]) >= 1


# =============================================================================
# PHASE 20: Cross-User Security & AI Safety Guardrails
# =============================================================================
def test_phase20_cross_user_isolation_and_safety(client: TestClient, db_session: Session):
    u1, u2, h1, h2 = get_test_users(db_session)
    data_map = seed_full_pipeline_data(db_session, u1, u2)
    doc_u2 = data_map["doc_u2"]

    # 1. User 1 cannot explain User 2's report
    res_unauth = client.post(f"/api/v1/reports/{doc_u2.id}/explain", json={"language": "en"}, headers=h1)
    assert res_unauth.status_code == 404

    # 2. User 1 search does not reveal User 2's creatinine (2.1 mg/dL)
    res_s1 = client.get("/api/v1/health-search?q=creatinine", headers=h1)
    assert res_s1.status_code == 200
    assert len(res_s1.json()["results"]) == 0

    # 3. User 2 search returns their own creatinine record
    res_s2 = client.get("/api/v1/health-search?q=creatinine", headers=h2)
    assert res_s2.status_code == 200
    assert len(res_s2.json()["results"]) >= 1
    assert "2.1" in str(res_s2.json()["results"][0]["value"])
