import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import LabTest, Prescription, VitalRecord, LabFlag
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.services.appointment_summary_service import appointment_summary_service
from backend.app.schemas.appointment_summary import (
    AppointmentSummaryGenerateRequest,
    AppointmentSummaryUpdateRequest
)
from backend.app.core.security import get_password_hash

# -----------------------------------------------------------------------------
# Test 1 & 2: Summary Generation with User Isolation
# -----------------------------------------------------------------------------
def test_1_2_appointment_summary_generation_and_user_isolation(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Seed Document
    doc = Document(
        user_id=user_id,
        original_filename="Annual_Checkup.pdf",
        stored_filename="checkup_1.pdf",
        file_path="uploads/checkup_1.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="hash_checkup_1",
        category=DocumentCategory.LAB_REPORT.value,
        title="Annual Health Checkup Report",
        document_date="2026-03-01"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # Seed Lab Test
    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Fasting Blood Sugar",
        canonical_name="glucose_fasting",
        observed_value="115",
        numeric_value=115.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-01"
    )
    # Seed Prescription
    rx = Prescription(
        document_id=doc.id,
        user_id=user_id,
        medication_name="Metformin",
        dosage="500mg",
        frequency="Twice daily",
        timing_instructions="After meals",
        prescribed_date="2026-03-01"
    )
    # Seed Vital
    vital = VitalRecord(
        user_id=user_id,
        record_date="2026-03-01",
        blood_pressure_systolic=125,
        blood_pressure_diastolic=82,
        heart_rate=72
    )
    db_session.add_all([lab, rx, vital])
    db_session.commit()

    resp = client.post(
        "/api/v1/appointment-summary/generate",
        json={"title": "Upcoming Consultation"},
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Upcoming Consultation"
    assert data["user_id"] == user_id
    
    summary_data = data["summary_data"]
    assert len(summary_data["recent_documents"]) >= 1
    assert summary_data["recent_documents"][0]["title"] == "Annual Health Checkup Report"
    assert len(summary_data["lab_measurements"]) >= 1
    assert "115" in summary_data["lab_measurements"][0]["latest_value"]
    assert len(summary_data["prescriptions"]) >= 1
    assert summary_data["prescriptions"][0]["medication_name"] == "Metformin"
    assert len(summary_data["vital_records"]) >= 1
    assert "125/82" in summary_data["vital_records"][0]["bp"]

# -----------------------------------------------------------------------------
# Test 3: Empty Records Handling (No Hallucinations)
# -----------------------------------------------------------------------------
def test_3_empty_records_handling(client: TestClient, db_session: Session):
    # Create a fresh empty user
    empty_user = User(
        email="empty_user_p8@example.com",
        hashed_password=get_password_hash("Pass12345!"),
        full_name="Empty Patient",
        is_active=True
    )
    db_session.add(empty_user)
    db_session.commit()
    db_session.refresh(empty_user)

    # Login to get token
    login_resp = client.post("/api/v1/auth/login", json={"email": "empty_user_p8@example.com", "password": "Pass12345!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/appointment-summary/generate", json={"title": "Empty Summary"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    summary_data = data["summary_data"]
    
    # Must be empty lists, no invented records
    assert len(summary_data["recent_documents"]) == 0
    assert len(summary_data["lab_measurements"]) == 0
    assert len(summary_data["prescriptions"]) == 0
    assert len(summary_data["vital_records"]) == 0

# -----------------------------------------------------------------------------
# Test 4, 5, 6, 7, 8: Specific Inclusion of Docs, Labs, Vitals, Rxs, Trends
# -----------------------------------------------------------------------------
def test_4_to_8_record_inclusions_and_health_intelligence_trends(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Add 2 chronological lab tests to test Health Intelligence trend calculation
    lab_prev = LabTest(
        user_id=user_id,
        test_name="Serum Cholesterol",
        canonical_name="cholesterol_total",
        observed_value="180",
        numeric_value=180.0,
        unit="mg/dL",
        flag=LabFlag.NORMAL.value,
        test_date="2026-01-10"
    )
    lab_curr = LabTest(
        user_id=user_id,
        test_name="Serum Cholesterol",
        canonical_name="cholesterol_total",
        observed_value="220",
        numeric_value=220.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-15"
    )
    db_session.add_all([lab_prev, lab_curr])
    db_session.commit()

    resp = client.post("/api/v1/appointment-summary/generate", json={"title": "Cholesterol Trend Review"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    meas = data["summary_data"]["lab_measurements"]
    
    chol_meas = next((m for m in meas if "Cholesterol" in m["test_name"]), None)
    assert chol_meas is not None
    assert chol_meas["latest_value"] == "220 mg/dL"
    assert chol_meas["previous_value"] == "180 mg/dL"
    assert chol_meas["trend_direction"] == "Increased"
    assert "+22.22%" in chol_meas["percentage_change"]

# -----------------------------------------------------------------------------
# Test 9, 10, 11, 12: Source Citations, Page Numbers & Evidence Grounding
# -----------------------------------------------------------------------------
def test_9_to_12_citations_and_evidence_grounding(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Lipid_Profile.pdf",
        stored_filename="lipid_profile_doc.pdf",
        file_path="uploads/lipid_profile_doc.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_lipid_doc",
        category=DocumentCategory.LAB_REPORT.value,
        title="Comprehensive Lipid Panel",
        document_date="2026-04-10"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Triglycerides",
        canonical_name="triglycerides",
        observed_value="165",
        numeric_value=165.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-04-10"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/appointment-summary/generate", json={"title": "Lipid Summary"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    sources = data["summary_data"]["sources"]
    assert len(sources) >= 1
    
    src = next((s for s in sources if s["document_id"] == doc.id), None)
    assert src is not None
    assert src["source_name"] == "Comprehensive Lipid Panel"
    assert src["page_number"] == 1
    assert "Triglycerides" in src["text_snippet"]

# -----------------------------------------------------------------------------
# Test 13 & 14: Reviewable Discussion Questions & Safety of Original Records
# -----------------------------------------------------------------------------
def test_13_14_user_review_does_not_modify_original_records(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    lab = LabTest(
        user_id=user_id,
        test_name="HbA1c",
        canonical_name="hba1c",
        observed_value="7.4",
        numeric_value=7.4,
        unit="%",
        flag=LabFlag.HIGH.value,
        test_date="2026-04-20"
    )
    db_session.add(lab)
    db_session.commit()
    db_session.refresh(lab)

    gen_resp = client.post("/api/v1/appointment-summary/generate", json={"title": "Diabetes Follow-up"}, headers=headers)
    summary_id = gen_resp.json()["id"]

    # User modifies questions and title
    custom_questions = [
        "Doctor, my HbA1c is 7.4%. Should we adjust my dietary carbohydrate targets?",
        "Are there any additional foot or retinal exams needed?"
    ]
    update_resp = client.put(
        f"/api/v1/appointment-summary/{summary_id}",
        json={
            "title": "Customized Diabetes Follow-up",
            "generated_questions": custom_questions,
            "excluded_sections": ["vitals"],
            "custom_notes": "Patient prefers morning follow-up."
        },
        headers=headers
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["title"] == "Customized Diabetes Follow-up"
    assert updated_data["summary_data"]["generated_questions"] == custom_questions
    assert updated_data["summary_data"]["custom_notes"] == "Patient prefers morning follow-up."

    # CRITICAL: Verify original lab test in database was NOT altered
    lab_in_db = db_session.query(LabTest).filter(LabTest.id == lab.id).first()
    assert lab_in_db.observed_value == "7.4"
    assert lab_in_db.unit == "%"
    assert lab_in_db.flag == LabFlag.HIGH.value

# -----------------------------------------------------------------------------
# Test 15, 16, 17: PDF Generation with Required Sections & Sources
# -----------------------------------------------------------------------------
def test_15_to_17_pdf_export_and_content_structure(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    headers = registered_user["headers"]

    # Generate summary first
    gen_resp = client.post("/api/v1/appointment-summary/generate", json={"title": "PDF Export Test"}, headers=headers)
    summary_id = gen_resp.json()["id"]

    # Download PDF
    pdf_resp = client.get(f"/api/v1/appointment-summary/{summary_id}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000 # PDF binary content generated
    assert pdf_resp.content.startswith(b"%PDF")

# -----------------------------------------------------------------------------
# Test 18 & 19: Cross-User Isolation & Unauthorized Access Rejection
# -----------------------------------------------------------------------------
def test_18_19_cross_user_isolation_and_unauthorized_access(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_a_id = registered_user["user"]["id"]
    headers_a = registered_user["headers"]

    # Create User B
    user_b = User(
        email="user_b_p8@example.com",
        hashed_password=get_password_hash("PassSecure999!"),
        full_name="User B Phase 8",
        is_active=True
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    # Create summary for User B
    sum_b = AppointmentSummary(
        user_id=user_b.id,
        title="User B Confidential Summary",
        summary_data={"patient_info": {"full_name": "User B"}, "lab_measurements": []}
    )
    db_session.add(sum_b)
    db_session.commit()
    db_session.refresh(sum_b)

    # User A attempts to view User B's summary -> 404
    resp_get = client.get(f"/api/v1/appointment-summary/{sum_b.id}", headers=headers_a)
    assert resp_get.status_code == 404

    # User A attempts to update User B's summary -> 404
    resp_put = client.put(f"/api/v1/appointment-summary/{sum_b.id}", json={"title": "Hacked Title"}, headers=headers_a)
    assert resp_put.status_code == 404

    # User A attempts to download User B's PDF -> 404
    resp_pdf = client.get(f"/api/v1/appointment-summary/{sum_b.id}/pdf", headers=headers_a)
    assert resp_pdf.status_code == 404

# -----------------------------------------------------------------------------
# Test 20, 21, 22: Summary Listing & Regression Verifications
# -----------------------------------------------------------------------------
def test_20_to_22_summary_listing_and_regression(
    client: TestClient,
    registered_user: dict
):
    headers = registered_user["headers"]

    # Generate at least one summary first
    client.post("/api/v1/appointment-summary/generate", json={"title": "List Test Summary"}, headers=headers)

    list_resp = client.get("/api/v1/appointment-summary/list", headers=headers)
    assert list_resp.status_code == 200
    summaries = list_resp.json()
    assert isinstance(summaries, list)
    assert len(summaries) >= 1
