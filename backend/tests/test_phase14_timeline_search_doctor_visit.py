import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.rag import RAGChunk
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.models.audit import AuditLog
from backend.app.core.security import create_access_token, get_password_hash

def get_or_create_users(db_session: Session):
    u1 = db_session.query(User).filter(User.email == "patient_p14_1@example.com").first()
    if not u1:
        u1 = User(
            email="patient_p14_1@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Patient Phase14 One",
            language_preference="en",
            is_active=True
        )
        db_session.add(u1)

    u2 = db_session.query(User).filter(User.email == "patient_p14_2@example.com").first()
    if not u2:
        u2 = User(
            email="patient_p14_2@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Patient Phase14 Two",
            language_preference="ta",
            is_active=True
        )
        db_session.add(u2)

    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    token1 = create_access_token(subject=str(u1.id))
    token2 = create_access_token(subject=str(u2.id))
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    return u1, u2, headers1, headers2

def seed_p14_data(db_session: Session, u1: User, u2: User):
    # User 1: Report 1 (Older)
    doc1 = Document(
        user_id=u1.id,
        original_filename="report_jan_2026.pdf",
        stored_filename="report_jan_2026.pdf",
        file_path="uploads/report_jan_2026.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_p14_doc1",
        category="lab_report",
        title="Comprehensive Metabolic Panel - Jan 2026",
        document_date="2026-01-10",
        clinic_or_lab="City Diagnostic Lab",
        doctor_name="Dr. Smith",
        ocr_status="completed",
        ocr_raw_text="Fasting Blood Glucose: 95 mg/dL. Hemoglobin A1c: 5.4%."
    )
    db_session.add(doc1)
    db_session.commit()
    db_session.refresh(doc1)

    t1 = LabTest(
        document_id=doc1.id,
        user_id=u1.id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose",
        test_category="metabolic",
        observed_value="95",
        unit="mg/dL",
        flag="normal",
        reference_range_text="70-99 mg/dL",
        reference_range_min=70.0,
        reference_range_max=99.0,
        confidence_score=0.98,
        test_date="2026-01-10"
    )
    t2 = LabTest(
        document_id=doc1.id,
        user_id=u1.id,
        test_name="Hemoglobin A1c",
        canonical_name="hba1c",
        test_category="glycemic",
        observed_value="5.4",
        unit="%",
        flag="normal",
        reference_range_text="4.0-5.6 %",
        reference_range_min=4.0,
        reference_range_max=5.6,
        confidence_score=0.97,
        test_date="2026-01-10"
    )
    db_session.add_all([t1, t2])

    # User 1: Report 2 (Newer - March 2026)
    doc2 = Document(
        user_id=u1.id,
        original_filename="report_mar_2026.pdf",
        stored_filename="report_mar_2026.pdf",
        file_path="uploads/report_mar_2026.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="hash_p14_doc2",
        category="lab_report",
        title="Blood Routine & Lipid Profile - Mar 2026",
        document_date="2026-03-15",
        clinic_or_lab="Apex Health Diagnostics",
        doctor_name="Dr. Taylor",
        ocr_status="completed",
        ocr_raw_text="Fasting Blood Glucose: 110 mg/dL. Total Cholesterol: 210 mg/dL."
    )
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    t3 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose",
        test_category="metabolic",
        observed_value="110",
        unit="mg/dL",
        flag="high",
        reference_range_text="70-99 mg/dL",
        reference_range_min=70.0,
        reference_range_max=99.0,
        confidence_score=0.99,
        test_date="2026-03-15"
    )
    t4 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="Total Cholesterol",
        canonical_name="total_cholesterol",
        test_category="lipid",
        observed_value="210",
        unit="mg/dL",
        flag="high",
        reference_range_text="< 200 mg/dL",
        reference_range_min=0.0,
        reference_range_max=200.0,
        confidence_score=0.96,
        test_date="2026-03-15"
    )
    db_session.add_all([t3, t4])

    # User 1: Prescription
    doc3 = Document(
        user_id=u1.id,
        original_filename="rx_mar_2026.pdf",
        stored_filename="rx_mar_2026.pdf",
        file_path="uploads/rx_mar_2026.pdf",
        file_size_bytes=512,
        mime_type="application/pdf",
        file_hash_sha256="hash_p14_doc3",
        category="prescription",
        title="Prescription Slip - Mar 2026",
        document_date="2026-03-20",
        clinic_or_lab="City Clinic",
        doctor_name="Dr. Taylor",
        ocr_status="completed",
        ocr_raw_text="Rx: Amoxicillin 500mg, 1 tablet twice daily for 7 days."
    )
    db_session.add(doc3)
    db_session.commit()
    db_session.refresh(doc3)

    rx1 = Prescription(
        document_id=doc3.id,
        user_id=u1.id,
        medication_name="Amoxicillin",
        dosage="500mg",
        frequency="Twice daily",
        timing_instructions="After food",
        duration="7 days",
        prescribed_date="2026-03-20"
    )
    db_session.add(rx1)

    # User 1: Vital Record
    vital1 = VitalRecord(
        user_id=u1.id,
        record_date="2026-03-22",
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        heart_rate=72,
        notes="Normal morning blood pressure."
    )
    db_session.add(vital1)

    # User 1: RAG Chunk for semantic search
    chunk1 = RAGChunk(
        user_id=u1.id,
        document_id=doc2.id,
        chunk_index=0,
        content="Patient has elevated fasting glucose levels measured in Apex Health Diagnostics report dated March 2026.",
        page_number=1
    )
    db_session.add(chunk1)

    # User 2: Isolated record
    doc_u2 = Document(
        user_id=u2.id,
        original_filename="u2_secret_report.pdf",
        stored_filename="u2_secret_report.pdf",
        file_path="uploads/u2_secret_report.pdf",
        file_size_bytes=1000,
        mime_type="application/pdf",
        file_hash_sha256="hash_p14_u2_doc",
        category="lab_report",
        title="User 2 Confidential Report",
        document_date="2026-03-25",
        ocr_status="completed",
        ocr_raw_text="User 2 thyroid panel TSH 2.5 mIU/L."
    )
    db_session.add(doc_u2)
    db_session.commit()
    db_session.refresh(doc_u2)

    t_u2 = LabTest(
        document_id=doc_u2.id,
        user_id=u2.id,
        test_name="Thyroid Stimulating Hormone",
        canonical_name="tsh",
        test_category="thyroid",
        observed_value="2.5",
        unit="mIU/L",
        flag="normal",
        test_date="2026-03-25"
    )
    db_session.add(t_u2)
    db_session.commit()

    return {
        "u1_doc1": doc1,
        "u1_doc2": doc2,
        "u1_doc3": doc3,
        "u2_doc": doc_u2
    }


def test_1_timeline_generation_and_sorting(client: TestClient, db_session: Session):
    """Verifies that the timeline aggregates documents, lab tests, prescriptions, and vitals ordered chronologically."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    res = client.get("/api/v1/health-timeline", headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert "events" in data
    assert data["total_events"] >= 5
    assert data["filtered_events_count"] >= 5

    # Check newest first sorting
    events = data["events"]
    dates = [e["event_date"] for e in events]
    assert dates[0] >= dates[-1]

    # Verify event types present
    types = {e["event_type"] for e in events}
    assert "REPORT" in types
    assert "LAB_TEST" in types
    assert "PRESCRIPTION" in types
    assert "VITALS" in types


def test_2_timeline_category_filters(client: TestClient, db_session: Session):
    """Verifies filtering by category (REPORTS, LAB_TESTS, PRESCRIPTIONS, VITALS)."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    # Filter by LAB_TESTS
    res_lab = client.get("/api/v1/health-timeline?category=LAB_TESTS", headers=h1)
    assert res_lab.status_code == 200
    for e in res_lab.json()["events"]:
        assert e["event_type"] == "LAB_TEST"

    # Filter by PRESCRIPTIONS
    res_rx = client.get("/api/v1/health-timeline?category=PRESCRIPTIONS", headers=h1)
    assert res_rx.status_code == 200
    for e in res_rx.json()["events"]:
        assert e["event_type"] == "PRESCRIPTION"

    # Filter by REPORTS
    res_rep = client.get("/api/v1/health-timeline?category=REPORTS", headers=h1)
    assert res_rep.status_code == 200
    for e in res_rep.json()["events"]:
        assert e["event_type"] == "REPORT"


def test_3_timeline_search_query_filter(client: TestClient, db_session: Session):
    """Verifies filtering timeline events by search keyword."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    res = client.get("/api/v1/health-timeline?q=Amoxicillin", headers=h1)
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) >= 1
    assert any("Amoxicillin" in e["title"] or "Amoxicillin" in e["summary"] for e in events)


def test_4_cross_user_timeline_isolation(client: TestClient, db_session: Session):
    """Ensures Patient 1 cannot see Patient 2's timeline events and vice versa."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    res1 = client.get("/api/v1/health-timeline", headers=h1)
    events1 = res1.json()["events"]
    for e in events1:
        assert "Thyroid" not in e["title"]
        assert "u2_secret" not in (e["source_document_title"] or "")

    res2 = client.get("/api/v1/health-timeline", headers=h2)
    events2 = res2.json()["events"]
    titles2 = [e["title"] for e in events2]
    assert any("Thyroid" in t for t in titles2)
    assert not any("Amoxicillin" in t for t in titles2)


def test_5_explain_my_report_structure_and_grounding(client: TestClient, db_session: Session):
    """Verifies Explain My Report endpoint formats structured grounded explanation."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    data_map = seed_p14_data(db_session, u1, u2)
    doc2 = data_map["u1_doc2"]

    res = client.post(
        f"/api/v1/reports/{doc2.id}/explain",
        json={"language": "en"},
        headers=h1
    )
    assert res.status_code == 200
    data = res.json()
    assert data["document_id"] == doc2.id
    assert data["evidence_status"] == "SUPPORTED"
    assert "REPORT OVERVIEW" in data["full_explanation"]
    assert "YOUR RECORDED VALUES" in data["full_explanation"]
    assert "WHAT CHANGED" in data["full_explanation"]
    assert "WHAT THE TEST GENERALLY MEASURES" in data["full_explanation"]
    assert "IMPORTANT" in data["full_explanation"]
    assert "SOURCES" in data["full_explanation"]
    assert len(data["citations"]) >= 1


def test_6_explain_my_report_multilingual(client: TestClient, db_session: Session):
    """Verifies Explain My Report in Tamil and Tanglish preserves clinical metrics."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    data_map = seed_p14_data(db_session, u1, u2)
    doc2 = data_map["u1_doc2"]
    
    # Tamil
    res_ta = client.post(
        f"/api/v1/reports/{doc2.id}/explain",
        json={"language": "ta"},
        headers=h1
    )
    assert res_ta.status_code == 200
    data_ta = res_ta.json()
    assert "110" in data_ta["full_explanation"] # Medical value preserved
    assert "mg/dL" in data_ta["full_explanation"] # Unit preserved

    # Tanglish
    res_tang = client.post(
        f"/api/v1/reports/{doc2.id}/explain",
        json={"language": "tanglish"},
        headers=h1
    )
    assert res_tang.status_code == 200
    data_tang = res_tang.json()
    assert "110" in data_tang["full_explanation"]
    assert "mg/dL" in data_tang["full_explanation"]


def test_7_explain_my_report_unauthorized_isolation(client: TestClient, db_session: Session):
    """Patient 1 cannot explain Patient 2's document."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    data_map = seed_p14_data(db_session, u1, u2)
    doc_u2 = data_map["u2_doc"]

    res = client.post(
        f"/api/v1/reports/{doc_u2.id}/explain",
        json={"language": "en"},
        headers=h1
    )
    assert res.status_code == 404


def test_8_global_search_hybrid_retrieval(client: TestClient, db_session: Session):
    """Verifies Global Search retrieves structured tests, medicines, dates, and semantic chunks."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    # Search by test name
    res_glucose = client.get("/api/v1/health-search?q=glucose", headers=h1)
    assert res_glucose.status_code == 200
    assert res_glucose.json()["total_results"] >= 1
    types_found = {r["result_type"] for r in res_glucose.json()["results"]}
    assert "LAB_TEST" in types_found or "DOCUMENT_CHUNK" in types_found

    # Search by medicine name
    res_amox = client.get("/api/v1/health-search?q=amoxicillin", headers=h1)
    assert res_amox.status_code == 200
    assert any(r["result_type"] == "PRESCRIPTION" for r in res_amox.json()["results"])

    # Search by date keyword
    res_mar = client.get("/api/v1/health-search?q=March", headers=h1)
    assert res_mar.status_code == 200
    assert res_mar.json()["total_results"] >= 1


def test_9_global_search_isolation(client: TestClient, db_session: Session):
    """Ensures search results never leak cross-user patient records."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    res1 = client.get("/api/v1/health-search?q=thyroid", headers=h1)
    assert res1.status_code == 200
    assert res1.json()["total_results"] == 0

    res2 = client.get("/api/v1/health-search?q=thyroid", headers=h2)
    assert res2.status_code == 200
    assert res2.json()["total_results"] >= 1


def test_10_doctor_visit_mode_summary(client: TestClient, db_session: Session):
    """Verifies Doctor Visit summary includes recent reports, medications, trends, and questions."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_p14_data(db_session, u1, u2)

    res = client.get("/api/v1/doctor-visit", headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert "recent_reports" in data
    assert "current_medications" in data
    assert "health_trends" in data
    assert "important_measurements" in data
    assert "questions_to_discuss" in data
    assert len(data["recent_reports"]) >= 1
    assert len(data["current_medications"]) >= 1
    assert len(data["important_measurements"]) >= 1 # High glucose/cholesterol flagged


def test_11_audit_logging_for_phase14_events(client: TestClient, db_session: Session):
    """Verifies that audit logs record TIMELINE_VIEWED, REPORT_EXPLAINED, GLOBAL_SEARCH_PERFORMED, and DOCTOR_VISIT_MODE_ACCESSED."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    data_map = seed_p14_data(db_session, u1, u2)
    doc2 = data_map["u1_doc2"]

    # Trigger events
    client.get("/api/v1/health-timeline", headers=h1)
    client.post(f"/api/v1/reports/{doc2.id}/explain", json={"language": "en"}, headers=h1)
    client.get("/api/v1/health-search?q=glucose", headers=h1)
    client.get("/api/v1/doctor-visit", headers=h1)

    actions = {log.action for log in db_session.query(AuditLog).filter(AuditLog.user_id == u1.id).all()}
    assert "TIMELINE_VIEWED" in actions
    assert "REPORT_EXPLAINED" in actions
    assert "GLOBAL_SEARCH_PERFORMED" in actions
    assert "DOCTOR_VISIT_MODE_ACCESSED" in actions
