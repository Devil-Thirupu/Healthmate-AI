import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory, OCRStatus
from backend.app.models.prescription_extraction import (
    PrescriptionExtraction, ExtractionCorrection, ConfidenceLevel, ParsingStatus
)
from backend.app.services.prescription_model_service import prescription_model_service
from backend.app.services.ocr_service import ocr_service

# -----------------------------------------------------------------------------
# Test 1: Clear Prescription (Printed Text with Doctor, Date, Medications)
# -----------------------------------------------------------------------------
def test_1_clear_prescription():
    raw_text = (
        "Apollo Hospitals Chennai\n"
        "Dr. Rajesh Kumar MBBS MD\n"
        "Date: 15/08/2026\n"
        "Patient: Suresh Raman\n"
        "Rx:\n"
        "1. Tab Paracetamol 650mg 1-0-1 5 days After Food\n"
        "2. Tab Pantoprazole 40mg 1-0-0 7 days Before Food\n"
    )
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy.png"),
        ocr_raw_text=raw_text,
        ocr_confidence_score=95.0
    )
    assert result["provider"] == "baseline_ocr"
    assert result["doctor_name"] == "Rajesh Kumar"
    assert "Apollo" in result["clinic_name"] or "Hospital" in result["clinic_name"]
    assert "15/08/2026" in result["prescription_date"]
    assert len(result["medications"]) >= 2
    assert result["confidence_level"] == ConfidenceLevel.HIGH.value
    assert result["parsing_status"] == ParsingStatus.SUCCESS.value

# -----------------------------------------------------------------------------
# Test 2: Handwritten Prescription (Noisy / Fragmented Text)
# -----------------------------------------------------------------------------
def test_2_handwritten_prescription():
    raw_text = "Dr Sharma\nTab Amoxicillin 500mg 1-0-1"
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy_hw.png"),
        ocr_raw_text=raw_text,
        ocr_confidence_score=65.0
    )
    assert result["doctor_name"] == "Sharma"
    assert len(result["medications"]) >= 1
    assert result["medications"][0]["drug_name"] == "Amoxicillin"
    assert result["confidence_level"] == ConfidenceLevel.MEDIUM.value

# -----------------------------------------------------------------------------
# Test 3: Poor-Quality Image (Minimal OCR Content)
# -----------------------------------------------------------------------------
def test_3_poor_quality_image():
    raw_text = "..."
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy_poor.png"),
        ocr_raw_text=raw_text,
        ocr_confidence_score=20.0
    )
    assert result["medications"] == []
    assert result["confidence_level"] == ConfidenceLevel.LOW.value
    assert result["parsing_status"] == ParsingStatus.NEEDS_USER_REVIEW.value
    assert result["doctor_name"] == "Not available in source"

# -----------------------------------------------------------------------------
# Test 4: Missing Dosage
# -----------------------------------------------------------------------------
def test_4_missing_dosage():
    raw_text = "Tab Azithromycin 1-0-0 3 days"
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy.png"),
        ocr_raw_text=raw_text
    )
    assert len(result["medications"]) >= 1
    med = result["medications"][0]
    assert med["drug_name"] == "Azithromycin"
    assert med["dosage"] == "Not available in source"
    assert med["duration"] == "3 days"

# -----------------------------------------------------------------------------
# Test 5: Missing Duration
# -----------------------------------------------------------------------------
def test_5_missing_duration():
    raw_text = "Tab Metformin 500mg BD"
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy.png"),
        ocr_raw_text=raw_text
    )
    assert len(result["medications"]) >= 1
    med = result["medications"][0]
    assert med["drug_name"] == "Metformin"
    assert med["dosage"] == "500mg"
    assert med["duration"] == "Not available in source"

# -----------------------------------------------------------------------------
# Test 6: Missing Medicine (Header Only)
# -----------------------------------------------------------------------------
def test_6_missing_medicine():
    raw_text = "Dr. Ananya Rao\nCity Clinic\nDate: 2026-08-30\nAdvice: Rest and hydration."
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy.png"),
        ocr_raw_text=raw_text
    )
    assert result["doctor_name"] == "Ananya Rao"
    assert result["clinic_name"] == "City Clinic"
    assert result["medications"] == []
    assert result["parsing_status"] == ParsingStatus.NEEDS_USER_REVIEW.value

# -----------------------------------------------------------------------------
# Test 7: Multiple Medicines
# -----------------------------------------------------------------------------
def test_7_multiple_medicines():
    raw_text = (
        "Rx:\n"
        "1. Tab Atorvastatin 20mg 0-0-1 30 days\n"
        "2. Tab Telmisartan 40mg 1-0-0 30 days\n"
        "3. Tab Aspirin 75mg 0-1-0 30 days\n"
    )
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=Path("dummy.png"),
        ocr_raw_text=raw_text
    )
    assert len(result["medications"]) == 3
    drugs = [m["drug_name"] for m in result["medications"]]
    assert "Atorvastatin" in drugs
    assert "Telmisartan" in drugs
    assert "Aspirin" in drugs

# -----------------------------------------------------------------------------
# Test 8: User Correction API Cycle
# -----------------------------------------------------------------------------
def test_8_user_correction(client: TestClient, registered_user: dict, db_session: Session):
    headers = registered_user["headers"]
    user_id = registered_user["user"]["id"]

    doc = Document(
        user_id=user_id,
        original_filename="rx_corr_test.png",
        stored_filename="rx_corr_111.png",
        file_path="uploads/rx_corr_111.png",
        file_size_bytes=1024,
        mime_type="image/png",
        file_hash_sha256="sha256_corr_test_001",
        category=DocumentCategory.PRESCRIPTION.value,
        title="Correction Test Rx",
        ocr_status=OCRStatus.COMPLETED.value,
        ocr_raw_text="Tab Amoxicilin 500mg 1-0-1"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # 1. Trigger extraction
    ext_resp = client.post(f"/api/v1/documents/{doc.id}/extract-model?provider=baseline_ocr", headers=headers)
    assert ext_resp.status_code == 200
    ext_id = ext_resp.json()["id"]

    # 2. Record field correction (e.g., misspelled drug name)
    corr_payload = {
        "field_name": "drug_name",
        "item_index": 0,
        "original_value": "Amoxicilin",
        "corrected_value": "Amoxicillin",
        "notes": "Fixed OCR spelling typo"
    }
    corr_resp = client.post(
        f"/api/v1/documents/{doc.id}/corrections/field?extraction_id={ext_id}",
        json=corr_payload,
        headers=headers
    )
    assert corr_resp.status_code == 200
    assert corr_resp.json()["corrected_value"] == "Amoxicillin"

    # 3. Retrieve history
    hist_resp = client.get(f"/api/v1/documents/{doc.id}/corrections/history", headers=headers)
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1
    assert hist_resp.json()[0]["original_value"] == "Amoxicilin"

# -----------------------------------------------------------------------------
# Test 9: Unauthorized Access & Security Isolation
# -----------------------------------------------------------------------------
def test_9_unauthorized_access(client: TestClient, registered_user: dict, db_session: Session):
    # Register user 2
    u2_resp = client.post("/api/v1/auth/register", json={
        "email": "user2_security@example.com",
        "password": "SecurePassword123!",
        "full_name": "User Two",
        "role": "patient"
    })
    user2_id = u2_resp.json()["user"]["id"]
    headers1 = registered_user["headers"]

    doc2 = Document(
        user_id=user2_id,
        original_filename="user2_private.png",
        stored_filename="user2_priv_123.png",
        file_path="uploads/user2_priv_123.png",
        file_size_bytes=1024,
        mime_type="image/png",
        file_hash_sha256="sha256_u2_priv",
        category=DocumentCategory.PRESCRIPTION.value,
        title="User 2 Confidential Rx"
    )
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    # User 1 tries to access user 2's extractions -> 404
    resp = client.get(f"/api/v1/documents/{doc2.id}/extractions", headers=headers1)
    assert resp.status_code == 404

    # User 1 tries to extract on user 2's doc -> 404
    resp = client.post(f"/api/v1/documents/{doc2.id}/extract-model", headers=headers1)
    assert resp.status_code == 404

# -----------------------------------------------------------------------------
# Test 10: Existing OCR Functionality & Fallback
# -----------------------------------------------------------------------------
def test_10_existing_ocr_fallback():
    # Verify ocr_service gracefully handles missing images / tesseract without crashes
    res = ocr_service.extract_from_image_file(Path("non_existent_file.png"))
    assert "full_text" in res
    assert isinstance(res["confidence_score"], (int, float))

# -----------------------------------------------------------------------------
# Test 11: Existing Document Upload Flow
# -----------------------------------------------------------------------------
def test_11_existing_document_upload(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]
    sample_content = b"PDF dummy content for upload verification"
    file_tuple = ("rx_upload_test.pdf", io.BytesIO(sample_content), "application/pdf")

    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={"title": "Lightweight Rx Upload", "category": "prescription", "doctor_name": "Dr. Varma"},
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Lightweight Rx Upload"
    assert data["category"] == "prescription"
    assert "id" in data

# -----------------------------------------------------------------------------
# Test 12: Existing Authentication
# -----------------------------------------------------------------------------
def test_12_existing_authentication(client: TestClient, registered_user: dict):
    # Unauthenticated request fails with 401
    resp = client.get("/api/v1/documents/")
    assert resp.status_code == 401

    # Authenticated request succeeds with 200
    resp = client.get("/api/v1/documents/", headers=registered_user["headers"])
    assert resp.status_code == 200

# -----------------------------------------------------------------------------
# Test 13: Existing Database Records Preserved
# -----------------------------------------------------------------------------
def test_13_existing_database_records(db_session: Session, registered_user: dict):
    # Query user count and ensure existing schema tables are queryable
    users = db_session.query(User).all()
    assert len(users) >= 1
    extractions = db_session.query(PrescriptionExtraction).all()
    assert isinstance(extractions, list)
