import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import LabTest, Prescription, LabFlag
from backend.app.models.rag import RAGChunk
from backend.app.services.gemini_service import gemini_service
from backend.app.core.config import settings

# -----------------------------------------------------------------------------
# Test 1: Ask Report Question (Grounded in Verified Lab/OCR Records)
# -----------------------------------------------------------------------------
def test_1_ask_report_question(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Complete_Blood_Count.pdf",
        stored_filename="cbc_report.pdf",
        file_path="uploads/cbc_report.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="sha256_cbc_test",
        category=DocumentCategory.LAB_REPORT.value,
        title="Complete Blood Count",
        document_date="2026-05-12"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Hemoglobin",
        canonical_name="hemoglobin",
        observed_value="14.2",
        numeric_value=14.2,
        unit="g/dL",
        reference_range_text="13.5 - 17.5 g/dL",
        flag=LabFlag.NORMAL.value,
        test_date="2026-05-12"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my hemoglobin value?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "PATIENT_FACTUAL"
    assert "14.2" in data["answer"]
    assert "g/dL" in data["answer"]
    assert data["evidence_status"] == "SUPPORTED"
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_name"] == "Complete Blood Count"

# -----------------------------------------------------------------------------
# Test 2: Compare Two Reports with Comparison Table Format
# -----------------------------------------------------------------------------
def test_2_compare_two_reports_table_format(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Report 1: Earlier Report
    doc1 = Document(
        user_id=user_id,
        original_filename="Blood_Panel_Jan.pdf",
        stored_filename="blood_jan.pdf",
        file_path="uploads/blood_jan.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="sha256_jan",
        category=DocumentCategory.LAB_REPORT.value,
        title="Blood Panel Jan",
        document_date="2026-01-15"
    )
    # Report 2: Current Report
    doc2 = Document(
        user_id=user_id,
        original_filename="Blood_Panel_June.pdf",
        stored_filename="blood_june.pdf",
        file_path="uploads/blood_june.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="sha256_june",
        category=DocumentCategory.LAB_REPORT.value,
        title="Blood Panel June",
        document_date="2026-06-20"
    )
    db_session.add_all([doc1, doc2])
    db_session.commit()

    lab1 = LabTest(
        document_id=doc1.id,
        user_id=user_id,
        test_name="Fasting Glucose",
        canonical_name="glucose_fasting",
        observed_value="110",
        numeric_value=110.0,
        unit="mg/dL",
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-01-15"
    )
    lab2 = LabTest(
        document_id=doc2.id,
        user_id=user_id,
        test_name="Fasting Glucose",
        canonical_name="glucose_fasting",
        observed_value="95",
        numeric_value=95.0,
        unit="mg/dL",
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.NORMAL.value,
        test_date="2026-06-20"
    )
    db_session.add_all([lab1, lab2])
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "Compare my two blood reports."}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "PATIENT_CHANGES"
    # Verify table header: Test | Previous | Current | Change | Reference Range
    assert "Test" in data["answer"]
    assert "Previous" in data["answer"]
    assert "Current" in data["answer"]
    assert "Change" in data["answer"]
    assert "Reference Range" in data["answer"]
    assert "Fasting Glucose" in data["answer"]

# -----------------------------------------------------------------------------
# Test 3: Ask Unsupported Question (Missing Information Rejection)
# -----------------------------------------------------------------------------
def test_3_unsupported_question_rejection(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]

    resp = client.post("/api/v1/assistant/chat", json={"query": "What does my MRI brain scan say?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "I couldn't find that information in your uploaded records." in data["answer"]
    assert data["evidence_status"] == "INSUFFICIENT"

# -----------------------------------------------------------------------------
# Test 4: Ask Medication Change Question (Strict Non-Prescriptive Safety Interception)
# -----------------------------------------------------------------------------
def test_4_medication_change_question_safety(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]

    test_queries = [
        "Should I change my medicine?",
        "Can I stop taking my metformin pills?",
        "Should I increase my dosage of aspirin?",
        "Please prescribe me a drug for headache"
    ]

    expected_safety_msg = (
        "I can explain and compare information from your medical records, but I cannot recommend "
        "changing your medication. Please discuss medication changes with your doctor."
    )

    for q in test_queries:
        resp = client.post("/api/v1/assistant/chat", json={"query": q}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert expected_safety_msg in data["answer"]
        assert data["evidence_priority_applied"] == "MEDICATION_SAFETY_GUARD_ACTIVE"

# -----------------------------------------------------------------------------
# Test 5: Verify Source Citations (Document Name, Date, Page/Section)
# -----------------------------------------------------------------------------
def test_5_verify_source_citation(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Thyroid_Profile_April.pdf",
        stored_filename="thyroid_april.pdf",
        file_path="uploads/thyroid_april.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_thyroid",
        category=DocumentCategory.LAB_REPORT.value,
        title="Thyroid Profile April",
        document_date="2026-04-10"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="TSH",
        canonical_name="tsh",
        observed_value="2.8",
        numeric_value=2.8,
        unit="uIU/mL",
        reference_range_text="0.4 - 4.2 uIU/mL",
        flag=LabFlag.NORMAL.value,
        test_date="2026-04-10"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my TSH value in my report?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) >= 1
    citation = data["citations"][0]
    assert citation["source_name"] == "Thyroid Profile April"
    assert citation["document_id"] == doc.id
    assert citation["page_number"] == 1
    assert "2.8" in citation["text_snippet"]

# -----------------------------------------------------------------------------
# Test 6: Security Verification - Backend Only Key & Never in Frontend Responses
# -----------------------------------------------------------------------------
def test_6_security_api_key_never_leaked_to_client(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my latest report?"}, headers=headers)
    assert resp.status_code == 200
    raw_response_text = resp.text

    # Ensure no API key variable or value appears anywhere in API payload
    assert "GEMINI_API_KEY" not in raw_response_text
    assert "VITE_GEMINI_API_KEY" not in raw_response_text
    if settings.GEMINI_API_KEY:
        assert settings.GEMINI_API_KEY not in raw_response_text

# -----------------------------------------------------------------------------
# Test 7: Low OCR Confidence Tagging Verification
# -----------------------------------------------------------------------------
def test_7_low_ocr_confidence_tagging():
    structured_items = [
        {
            "source_name": "Unclear_Scan.pdf",
            "document_id": 99,
            "page_number": 1,
            "confidence": 45.0,  # Low confidence (< 70%)
            "data": {
                "type": "lab_test",
                "test_name": "Creatinine",
                "value": "1.1",
                "unit": "mg/dL",
                "reference_range": "0.7 - 1.3 mg/dL",
                "date": "2026-03-01",
                "flag": "normal"
            }
        }
    ]
    context = gemini_service.format_evidence_context(structured_items, [], [])
    assert "[Needs Verification - Low OCR Confidence]" in context

# -----------------------------------------------------------------------------
# Test 8: Gemini Model Dispatch & Fallback Execution
# -----------------------------------------------------------------------------
def test_8_gemini_service_dispatch_and_guard(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_gemini_api_key_12345")
    assert gemini_service.is_configured is True

    # Test medication change safety interceptor
    med_reply = gemini_service.generate_chat_response(
        query="Should I change my medicine?",
        user_structured=[],
        user_doc_chunks=[],
        general_knowledge=[],
        language="en"
    )
    assert "cannot recommend changing your medication" in med_reply

    # Test unsupported question
    unsupported_reply = gemini_service.generate_chat_response(
        query="What is my MRI brain scan?",
        user_structured=[],
        user_doc_chunks=[],
        general_knowledge=[]
    )
    assert "I couldn't find that information in your uploaded records." in unsupported_reply
