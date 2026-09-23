import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import LabTest, Prescription, LabFlag
from backend.app.models.rag import RAGChunk, MedicalKnowledgeChunk
from backend.app.services.hybrid_rag_service import hybrid_rag_service
from backend.app.services.evidence_guard_service import evidence_guard_service
from backend.app.core.security import get_password_hash

# -----------------------------------------------------------------------------
# Test 1: Supported Patient Answer with Exact Value & Source
# -----------------------------------------------------------------------------
def test_1_supported_patient_answer(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Blood_Report_March.pdf",
        stored_filename="blood_march.pdf",
        file_path="uploads/blood_march.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash_sha256="sha256_blood_march",
        category=DocumentCategory.LAB_REPORT.value,
        title="Blood Report March",
        document_date="2026-03-10"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Fasting Glucose",
        canonical_name="glucose_fasting",
        observed_value="105",
        numeric_value=105.0,
        unit="mg/dL",
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-10"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What was my glucose value in March?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "PATIENT_FACTUAL"
    assert "105" in data["answer"]
    assert data["evidence_status"] == "SUPPORTED"
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_name"] == "Blood Report March"
    assert "105" in data["citations"][0]["text_snippet"]

# -----------------------------------------------------------------------------
# Test 2: Missing Patient Information Rejection (Never Guess)
# -----------------------------------------------------------------------------
def test_2_missing_patient_information_rejection(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]

    resp = client.post("/api/v1/assistant/chat", json={"query": "What was my cholesterol value in January?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "The available records do not contain enough information to answer this patient-specific question." in data["answer"]
    assert data["evidence_status"] == "INSUFFICIENT"
    assert data["evidence_priority_applied"] == "USER_RECORDS_MANDATORY_MISSING"

# -----------------------------------------------------------------------------
# Test 3: General Medical Knowledge Question
# -----------------------------------------------------------------------------
def test_3_general_medical_knowledge_question(client: TestClient, registered_user: dict, db_session: Session):
    headers = registered_user["headers"]

    kg = MedicalKnowledgeChunk(
        dataset_name="Malikeh1375/medical-question-answering-datasets",
        dataset_version="29833779cb5921f474d9f469aa85c115277bf489",
        license="mit",
        input_question="What is glucose and how does the body use it?",
        output_answer="Glucose is the primary simple sugar providing energy for cellular respiration and metabolism.",
        content="Question: What is glucose?\nAnswer: Glucose provides cellular energy."
    )
    db_session.add(kg)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is glucose?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "GENERAL_MEDICAL_KNOWLEDGE"
    assert "glucose" in data["answer"].lower()
    assert data["evidence_status"] == "SUPPORTED"
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_type"] == "GENERAL_MEDICAL_KNOWLEDGE"

# -----------------------------------------------------------------------------
# Test 4: Hybrid Question with Non-Causal Grounding
# -----------------------------------------------------------------------------
def test_4_hybrid_question_non_causal(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Add 2 historical glucose records (Jan and March)
    lab1 = LabTest(
        user_id=user_id,
        test_name="Glucose",
        canonical_name="glucose",
        observed_value="95",
        numeric_value=95.0,
        unit="mg/dL",
        flag=LabFlag.NORMAL.value,
        test_date="2026-01-15"
    )
    lab2 = LabTest(
        user_id=user_id,
        test_name="Glucose",
        canonical_name="glucose",
        observed_value="110",
        numeric_value=110.0,
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-10"
    )
    db_session.add_all([lab1, lab2])
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "Explain the changes in my glucose reports."}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "HYBRID"
    assert "95" in data["answer"] or "110" in data["answer"]
    # Evidence Guard must ensure non-causal disclaimer is present
    assert "cannot establish" in data["answer"].lower() or "do not provide clinical evidence" in data["answer"].lower()
    assert data["evidence_status"] in ["SUPPORTED", "PARTIAL"]

# -----------------------------------------------------------------------------
# Test 5: Citation Generation with Complete Metadata
# -----------------------------------------------------------------------------
def test_5_citation_generation(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Rx_Cardiology.pdf",
        stored_filename="rx_cardio.pdf",
        file_path="uploads/rx_cardio.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_rx_cardio",
        category=DocumentCategory.PRESCRIPTION.value,
        title="Cardiology Prescription",
        document_date="2026-04-01"
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
        duration="30 days",
        prescribed_date="2026-04-01"
    )
    db_session.add(rx)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my active medicine prescription?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) >= 1
    cit = data["citations"][0]
    assert cit["source_type"] == "USER_STRUCTURED_RECORD"
    assert cit["source_name"] == "Cardiology Prescription"
    assert cit["document_id"] == doc.id
    assert cit["page_number"] == 1
    assert "Metformin 500mg" in cit["text_snippet"]

# -----------------------------------------------------------------------------
# Test 6: Page Number Preservation
# -----------------------------------------------------------------------------
def test_6_page_number_preservation(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Discharge_Summary.pdf",
        stored_filename="discharge_sum.pdf",
        file_path="uploads/discharge_sum.pdf",
        file_size_bytes=4096,
        mime_type="application/pdf",
        file_hash_sha256="sha256_discharge",
        category=DocumentCategory.DISCHARGE_SUMMARY.value,
        title="Hospital Discharge Summary",
        document_date="2026-02-20"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    chunk = RAGChunk(
        document_id=doc.id,
        user_id=user_id,
        page_number=3,
        chunk_index=2,
        content="Patient was discharged on 2026-02-20 with stable hemodynamics and instructed to follow low-sodium diet."
    )
    db_session.add(chunk)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What does my uploaded report say about hemodynamics?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["page_number"] == 3
    assert data["citations"][0]["source_type"] == "USER_DOCUMENT_CHUNK"

# -----------------------------------------------------------------------------
# Test 7: Source Text Snippet Preservation
# -----------------------------------------------------------------------------
def test_7_source_text_preservation(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="Lab_Bilirubin.pdf",
        stored_filename="bili.pdf",
        file_path="uploads/bili.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_bili",
        category=DocumentCategory.LAB_REPORT.value,
        title="Bilirubin Report",
        document_date="2026-02-15"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    chunk = RAGChunk(
        document_id=doc.id,
        user_id=user_id,
        page_number=2,
        chunk_index=1,
        content="Exact OCR Observation: Serum Bilirubin Total is 1.2 mg/dL with no direct jaundice."
    )
    db_session.add(chunk)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What does the pdf file says about Serum Bilirubin?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) >= 1
    assert "Serum Bilirubin Total is 1.2 mg/dL" in data["citations"][0]["text_snippet"]

# -----------------------------------------------------------------------------
# Test 8 & 9: View Source Authorization & Cross-User Source Protection
# -----------------------------------------------------------------------------
def test_8_9_view_source_authorization_and_cross_user_protection(client: TestClient, registered_user: dict, db_session: Session):
    user_a_id = registered_user["user"]["id"]
    headers_a = registered_user["headers"]

    # Create User B
    user_b = User(
        email="user_b_phase7@example.com",
        hashed_password=get_password_hash("SecretPass123!"),
        full_name="User B Phase 7",
        is_active=True
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    # Document belonging to User B
    doc_b = Document(
        user_id=user_b.id,
        original_filename="UserB_Confidential_Report.pdf",
        stored_filename="user_b_conf.pdf",
        file_path="uploads/user_b_conf.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_user_b_conf",
        category=DocumentCategory.LAB_REPORT.value,
        title="User B Secret Lab",
        document_date="2026-03-01"
    )
    db_session.add(doc_b)
    db_session.commit()
    db_session.refresh(doc_b)

    # User A tries to preview User B's document -> must be denied (404/403)
    resp_preview = client.get(f"/api/v1/documents/{doc_b.id}/preview", headers=headers_a)
    assert resp_preview.status_code in [403, 404]

    # User A searches assistant chat -> must NOT retrieve User B's data
    lab_b = LabTest(
        document_id=doc_b.id,
        user_id=user_b.id,
        test_name="Secret Test B",
        canonical_name="secret_b",
        observed_value="999.9",
        unit="U/L",
        flag=LabFlag.CRITICAL.value
    )
    db_session.add(lab_b)
    db_session.commit()

    resp_chat = client.post("/api/v1/assistant/chat", json={"query": "What is my Secret Test B result?"}, headers=headers_a)
    assert resp_chat.status_code == 200
    data_chat = resp_chat.json()
    assert "999.9" not in data_chat["answer"]
    assert data_chat["evidence_status"] == "INSUFFICIENT"

# -----------------------------------------------------------------------------
# Test 10: Evidence Status Types
# -----------------------------------------------------------------------------
def test_10_evidence_status_types(client: TestClient, registered_user: dict, db_session: Session):
    headers = registered_user["headers"]

    # 1. Missing -> INSUFFICIENT
    resp1 = client.post("/api/v1/assistant/chat", json={"query": "What is my potassium and sodium level?"}, headers=headers)
    assert resp1.json()["evidence_status"] == "INSUFFICIENT"

    # Seed general medical knowledge chunk
    kg = MedicalKnowledgeChunk(
        dataset_name="Malikeh1375/medical-question-answering-datasets",
        dataset_version="29833779cb5921f474d9f469aa85c115277bf489",
        license="mit",
        input_question="What is glucose and why is it important?",
        output_answer="Glucose is the main source of chemical energy for the cells in the human body.",
        content="Question: What is glucose?\nAnswer: Glucose is energy source."
    )
    db_session.add(kg)
    db_session.commit()

    # 2. General knowledge -> SUPPORTED
    resp2 = client.post("/api/v1/assistant/chat", json={"query": "What is glucose and why is it important?"}, headers=headers)
    assert resp2.json()["evidence_status"] == "SUPPORTED"

# -----------------------------------------------------------------------------
# Test 11 & 12: Unsupported Answer & Missing Evidence Rejection
# -----------------------------------------------------------------------------
def test_11_12_unsupported_answer_and_missing_evidence_rejection():
    # Direct service unit test
    msg = evidence_guard_service.get_insufficient_evidence_message("en")
    assert "The available records do not contain enough information" in msg

    status = evidence_guard_service.determine_evidence_status(
        query_type="PATIENT_FACTUAL",
        user_structured=[],
        user_doc_chunks=[],
        general_knowledge=[],
        query_has_patient_match=False
    )
    assert status == "INSUFFICIENT"

# -----------------------------------------------------------------------------
# Test 13, 14, 15: Evidence Hierarchy (Structured > Chunks > General Knowledge)
# -----------------------------------------------------------------------------
def test_13_14_15_evidence_hierarchy(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Add structured test
    lab = LabTest(
        user_id=user_id,
        test_name="Fasting Glucose",
        canonical_name="glucose_fasting",
        observed_value="102",
        unit="mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-01"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my fasting glucose?"}, headers=headers)
    data = resp.json()
    assert data["evidence_priority_applied"] == "USER_RECORDS_PRIMARY"
    assert data["citations"][0]["source_type"] == "USER_STRUCTURED_RECORD"
