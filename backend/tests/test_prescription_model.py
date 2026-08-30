import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory, OCRStatus
from backend.app.models.prescription_extraction import PrescriptionExtraction, ExtractionCorrection, ConfidenceLevel, ParsingStatus
from backend.app.services.prescription_model_service import prescription_model_service

def test_safe_json_parsing():
    """Verify safe JSON parsing rejects malformed input and flags for user review instead of guessing."""
    valid_json = '{"doctor_name": "Dr. Sharma", "medications": [{"drug_name": "Amoxicillin"}]}'
    parsed, status = prescription_model_service.safe_parse_json(valid_json)
    assert status == ParsingStatus.SUCCESS.value
    assert parsed["doctor_name"] == "Dr. Sharma"

    # Markdown wrapped json
    markdown_json = '```json\n{"doctor_name": "Dr. Patel"}\n```'
    parsed, status = prescription_model_service.safe_parse_json(markdown_json)
    assert status == ParsingStatus.SUCCESS.value
    assert parsed["doctor_name"] == "Dr. Patel"

    # Malformed unparseable output
    malformed = "Dr. Sharma prescribed some tabs without valid json syntax"
    parsed, status = prescription_model_service.safe_parse_json(malformed)
    assert parsed is None
    assert status == ParsingStatus.NEEDS_USER_REVIEW.value

def test_zero_hallucination_sanitization():
    """Verify missing or empty values are strictly replaced with 'Not available in source'."""
    assert prescription_model_service.sanitize_field(None) == "Not available in source"
    assert prescription_model_service.sanitize_field("") == "Not available in source"
    assert prescription_model_service.sanitize_field("null") == "Not available in source"
    assert prescription_model_service.sanitize_field("500mg") == "500mg"

def test_confidence_never_invented():
    """Verify confidence score is None and confidence_level is NOT_AVAILABLE when not probabilistic."""
    res = prescription_model_service.extract_with_baseline_provider(Path("dummy.png"), "Tab Metformin 500mg")
    assert res["confidence_score"] is None
    assert res["confidence_level"] == ConfidenceLevel.NOT_AVAILABLE.value

def test_normalize_medicine_name_preserves_original():
    """Verify normalization returns canonical drug while original remains untouched."""
    raw = "Tab. Metformin 500mg"
    norm = prescription_model_service.normalize_medicine_name(raw)
    assert norm == "Metformin"

    # Structure medications preserves both
    meds = prescription_model_service.structure_medications([{"drug_name": raw, "dosage": "500mg"}])
    assert len(meds) == 1
    assert meds[0]["drug_name"] == raw
    assert meds[0]["normalized_name"] == "Metformin"
    assert meds[0]["dosage"] == "500mg"

def test_prescription_extraction_api_and_correction(client: TestClient, registered_user: dict, db_session: Session):
    """Test full API cycle: create doc, get extractions, add field correction, confirm user review."""
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # 1. Create a dummy prescription document
    doc = Document(
        user_id=user_id,
        original_filename="rx_test.png",
        stored_filename="rx_test_123.png",
        file_path="uploads/rx_test_123.png",
        file_size_bytes=1024,
        mime_type="image/png",
        file_hash_sha256="test_sha_hash_12345",
        category=DocumentCategory.PRESCRIPTION.value,
        title="Test Prescription",
        ocr_status=OCRStatus.COMPLETED.value,
        ocr_raw_text="Tab Azithromycin 500mg 1-0-0 5 days"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # 2. Trigger baseline model extraction API
    resp = client.post(f"/api/v1/documents/{doc.id}/extract-model?provider=baseline_ocr", headers=headers)
    assert resp.status_code == 200
    ext_data = resp.json()
    assert ext_data["provider"] == "baseline_ocr"
    assert ext_data["confidence_level"] == "NOT_AVAILABLE"
    extraction_id = ext_data["id"]

    # 3. Retrieve extractions
    list_resp = client.get(f"/api/v1/documents/{doc.id}/extractions", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 4. Record a field correction
    corr_payload = {
        "field_name": "dosage",
        "item_index": 0,
        "original_value": "500mg",
        "corrected_value": "250mg",
        "notes": "Patient dose adjustment"
    }
    corr_resp = client.post(
        f"/api/v1/documents/{doc.id}/corrections/field?extraction_id={extraction_id}",
        json=corr_payload,
        headers=headers
    )
    assert corr_resp.status_code == 200
    assert corr_resp.json()["corrected_value"] == "250mg"

    # 5. Retrieve correction history
    hist_resp = client.get(f"/api/v1/documents/{doc.id}/corrections/history", headers=headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 1
    assert history[0]["field_name"] == "dosage"
    assert history[0]["corrected_value"] == "250mg"

    # 6. Confirm user review
    confirm_payload = {
        "notes": "User confirmed all fields",
        "medications": [
            {
                "drug_name": "Tab Azithromycin",
                "normalized_name": "Azithromycin",
                "dosage": "250mg",
                "frequency": "Once daily (OD)",
                "duration": "5 days",
                "instructions": "After food",
                "confidence": None
            }
        ]
    }
    conf_resp = client.post(
        f"/api/v1/documents/{doc.id}/confirm-review?extraction_id={extraction_id}",
        json=confirm_payload,
        headers=headers
    )
    assert conf_resp.status_code == 200
    assert conf_resp.json()["is_user_reviewed"] is True

def test_cross_user_security_isolation(client: TestClient, registered_user: dict, db_session: Session):
    """Verify user cannot access or modify another user's prescription extractions."""
    # Register a second user
    u2_resp = client.post("/api/v1/auth/register", json={
        "email": "patient2@example.com",
        "password": "SecurePassword123!",
        "full_name": "Second Patient",
        "role": "patient"
    })
    user2_id = u2_resp.json()["user"]["id"]
    headers1 = registered_user["headers"]

    # Create document for user 2
    doc2 = Document(
        user_id=user2_id,
        original_filename="user2_rx.png",
        stored_filename="user2_rx_999.png",
        file_path="uploads/user2_rx_999.png",
        file_size_bytes=1024,
        mime_type="image/png",
        file_hash_sha256="test_sha_user2",
        category=DocumentCategory.PRESCRIPTION.value,
        title="User 2 Secret Rx"
    )
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    # User 1 attempts to access user 2's extractions -> 404
    resp = client.get(f"/api/v1/documents/{doc2.id}/extractions", headers=headers1)
    assert resp.status_code == 404

    # User 1 attempts to record field correction on user 2's doc -> 404
    corr_resp = client.post(
        f"/api/v1/documents/{doc2.id}/corrections/field",
        json={"field_name": "dosage", "item_index": 0, "corrected_value": "10mg"},
        headers=headers1
    )
    assert corr_resp.status_code == 404
