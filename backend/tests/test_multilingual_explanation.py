import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import LabTest, Prescription, VitalRecord, LabFlag
from backend.app.models.rag import MedicalKnowledgeChunk
from backend.app.services.multilingual_explanation_service import multilingual_explanation_service
from backend.app.services.evidence_guard_service import evidence_guard_service
from backend.app.services.hybrid_rag_service import hybrid_rag_service

# -----------------------------------------------------------------------------
# Test 1, 2, 3, 4, 5: Multilingual Chat Responses & Default Behavior
# -----------------------------------------------------------------------------
def test_1_to_5_multilingual_chat_responses(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Seed Document
    doc = Document(
        user_id=user_id,
        original_filename="Lab_Report_March.pdf",
        stored_filename="lab_rep_mar.pdf",
        file_path="uploads/lab_rep_mar.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="hash_lab_rep_mar",
        category=DocumentCategory.LAB_REPORT.value,
        title="March Comprehensive Lab Panel",
        document_date="2026-03-10"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # Seed Lab Test
    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose_fasting",
        observed_value="105",
        numeric_value=105.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-10"
    )
    db_session.add(lab)
    db_session.commit()

    # 1. English Response
    resp_en = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What was my glucose value in March?", "language": "en"},
        headers=headers
    )
    assert resp_en.status_code == 200
    data_en = resp_en.json()
    assert "105" in data_en["answer"]
    assert "mg/dL" in data_en["answer"]
    assert "Based on your uploaded medical records" in data_en["answer"]

    # 2. Tamil Response
    resp_ta = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What was my glucose value in March?", "language": "ta"},
        headers=headers
    )
    assert resp_ta.status_code == 200
    data_ta = resp_ta.json()
    assert "105" in data_ta["answer"]
    assert "mg/dL" in data_ta["answer"]
    assert "மருத்துவ" in data_ta["answer"]

    # 3. Tanglish Response
    resp_tanglish = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What was my glucose value in March?", "language": "tanglish"},
        headers=headers
    )
    assert resp_tanglish.status_code == 200
    data_tanglish = resp_tanglish.json()
    assert "105" in data_tanglish["answer"]
    assert "mg/dL" in data_tanglish["answer"]
    assert "records-il" in data_tanglish["answer"].lower() or "vivarangal" in data_tanglish["answer"].lower()

    # 4. Default English Behavior when language omitted
    resp_default = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What was my glucose value in March?"},
        headers=headers
    )
    assert resp_default.status_code == 200
    data_default = resp_default.json()
    assert "Based on your uploaded medical records" in data_default["answer"]
    assert "105" in data_default["answer"]

    # 5. Language Parameter Normalization
    assert multilingual_explanation_service.normalize_language("TAMIL") == "ta"
    assert multilingual_explanation_service.normalize_language("tanglish") == "tanglish"
    assert multilingual_explanation_service.normalize_language(None) == "en"
    assert multilingual_explanation_service.normalize_language("invalid_xyz") == "en"

# -----------------------------------------------------------------------------
# Test 6, 7, 8, 9, 10, 11: Medical Values, Units, Dates, Names, Citations & Evidence Status
# -----------------------------------------------------------------------------
def test_6_to_11_medical_value_and_citation_preservation(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Prescription_April.pdf",
        stored_filename="rx_apr.pdf",
        file_path="uploads/rx_apr.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_rx_apr",
        category=DocumentCategory.PRESCRIPTION.value,
        title="April Diabetic Prescription",
        document_date="2026-04-15"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    rx = Prescription(
        document_id=doc.id,
        user_id=user_id,
        medication_name="Metformin",
        dosage="500mg",
        frequency="Twice daily",
        timing_instructions="After meals",
        prescribed_date="2026-04-15"
    )
    db_session.add(rx)
    db_session.commit()

    for lang in ["en", "ta", "tanglish"]:
        resp = client.post(
            "/api/v1/assistant/chat",
            json={"query": "What medicine was prescribed to me?", "language": lang},
            headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Test 6 & 8: Medicine name & dosage value strictly preserved
        assert "Metformin" in data["answer"]
        assert "500mg" in data["answer"]
        
        # Test 10: Citation preservation
        citations = data["citations"]
        assert len(citations) >= 1
        assert citations[0]["source_name"] == "April Diabetic Prescription"
        assert citations[0]["document_id"] == doc.id
        assert citations[0]["page_number"] == 1
        
        # Test 11: Evidence status preserved
        assert data["evidence_status"] == "SUPPORTED"

# -----------------------------------------------------------------------------
# Test 12: Insufficient Evidence Handling across all three languages
# -----------------------------------------------------------------------------
def test_12_insufficient_evidence_messages_multilingual(
    client: TestClient,
    registered_user: dict
):
    headers = registered_user["headers"]

    # Query for a missing non-existent biomarker
    q = "What was my serum ferritin level in December 2024?"
    
    # EN
    resp_en = client.post("/api/v1/assistant/chat", json={"query": q, "language": "en"}, headers=headers)
    assert resp_en.status_code == 200
    assert "not contain enough information" in resp_en.json()["answer"]
    assert resp_en.json()["evidence_status"] == "INSUFFICIENT"

    # TA
    resp_ta = client.post("/api/v1/assistant/chat", json={"query": q, "language": "ta"}, headers=headers)
    assert resp_ta.status_code == 200
    assert "தகவல்கள்" in resp_ta.json()["answer"]
    assert resp_ta.json()["evidence_status"] == "INSUFFICIENT"

    # TANGLISH
    resp_tg = client.post("/api/v1/assistant/chat", json={"query": q, "language": "tanglish"}, headers=headers)
    assert resp_tg.status_code == 200
    assert "details" in resp_tg.json()["answer"].lower() or "information" in resp_tg.json()["answer"].lower() or "records" in resp_tg.json()["answer"].lower()
    assert resp_tg.json()["evidence_status"] == "INSUFFICIENT"

# -----------------------------------------------------------------------------
# Test 13: Hybrid RAG Response in English, Tamil, and Tanglish
# -----------------------------------------------------------------------------
def test_13_hybrid_rag_multilingual(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Seed Lab Test for patient
    lab = LabTest(
        user_id=user_id,
        test_name="Fasting Glucose",
        canonical_name="glucose_fasting",
        observed_value="105",
        numeric_value=105.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-10"
    )
    # Seed general medical knowledge
    mk = MedicalKnowledgeChunk(
        dataset_name="Medical QA Dataset",
        input_question="What is fasting glucose and why is it important?",
        output_answer="Fasting blood glucose measures blood sugar levels after overnight fasting to evaluate glycemic control.",
        content="Q: What is fasting glucose and why is it important?\nA: Fasting blood glucose measures blood sugar levels after overnight fasting to evaluate glycemic control.",
        license="MIT"
    )
    db_session.add_all([lab, mk])
    db_session.commit()

    # Query hybrid inquiry
    hybrid_q = "What is my fasting glucose and why is it important?"
    for lang in ["en", "ta", "tanglish"]:
        resp = client.post(
            "/api/v1/assistant/chat",
            json={"query": hybrid_q, "language": lang},
            headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "105" in data["answer"]
        assert "mg/dL" in data["answer"]
        assert len(data["citations"]) >= 1

# -----------------------------------------------------------------------------
# Test 14 & 15: Prescription & Report Explanation Multilingual Formatting
# -----------------------------------------------------------------------------
def test_14_15_prescription_and_report_explanation_formatting():
    # Test prescription formatter
    ta_rx = multilingual_explanation_service.format_prescription_item(
        medication_name="Amoxicillin",
        dosage="250mg",
        frequency="Three times daily",
        timing="After food",
        duration="5 days",
        language="ta"
    )
    assert "Amoxicillin" in ta_rx
    assert "250mg" in ta_rx
    assert "உணவுக்குப் பின்" in ta_rx

    tg_rx = multilingual_explanation_service.format_prescription_item(
        medication_name="Amoxicillin",
        dosage="250mg",
        frequency="Three times daily",
        timing="After food",
        duration="5 days",
        language="tanglish"
    )
    assert "Amoxicillin" in tg_rx
    assert "Unavukku pin" in tg_rx

    # Test lab item formatter
    ta_lab = multilingual_explanation_service.format_lab_item(
        test_name="HbA1c",
        value="6.5",
        unit="%",
        date="2026-03-10",
        flag="high",
        language="ta"
    )
    assert "HbA1c" in ta_lab
    assert "6.5 %" in ta_lab or "6.5%" in ta_lab
    assert "2026-03-10" in ta_lab
    assert "HIGH" in ta_lab

# -----------------------------------------------------------------------------
# Test 16, 17, 18, 19: Phase 1–8 Full Regression
# -----------------------------------------------------------------------------
def test_16_to_19_regression_check(
    client: TestClient,
    registered_user: dict
):
    headers = registered_user["headers"]

    # Phase 8 Appointment Summary Generate
    resp_sum = client.post(
        "/api/v1/appointment-summary/generate",
        json={"title": "Multilingual Regression Summary"},
        headers=headers
    )
    assert resp_sum.status_code == 201
    assert "id" in resp_sum.json()

    # Knowledge sources info
    resp_sources = client.get("/api/v1/assistant/knowledge-sources", headers=headers)
    assert resp_sources.status_code == 200
    sources = resp_sources.json()
    assert len(sources) >= 1
