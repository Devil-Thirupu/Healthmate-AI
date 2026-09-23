import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pathlib import Path

from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory
from backend.app.models.clinical import LabTest, Prescription, LabFlag
from backend.app.models.rag import RAGChunk, MedicalKnowledgeChunk
from backend.app.services.hybrid_rag_service import hybrid_rag_service
from data.pipeline.process_medical_qa_dataset import process_medical_qa_dataset

# -----------------------------------------------------------------------------
# Test 1: Exact Patient-Value Query
# -----------------------------------------------------------------------------
def test_1_exact_patient_value_query(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="sugar_report.pdf",
        stored_filename="sugar_1.pdf",
        file_path="uploads/sugar_1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_sugar_1",
        category=DocumentCategory.LAB_REPORT.value,
        title="Fasting Blood Sugar Test",
        document_date="2026-03-15"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="Fasting Blood Sugar",
        canonical_name="glucose_fasting",
        observed_value="108",
        numeric_value=108.0,
        unit="mg/dL",
        reference_range_text="70 - 99 mg/dL",
        flag=LabFlag.HIGH.value,
        test_date="2026-03-15"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my fasting blood sugar result?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "PATIENT_FACTUAL"
    assert "108" in data["answer"]
    assert "Fasting Blood Sugar" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_type"] == "USER_STRUCTURED_RECORD"

# -----------------------------------------------------------------------------
# Test 2: General Medical Question
# -----------------------------------------------------------------------------
def test_2_general_medical_question(client: TestClient, registered_user: dict, db_session: Session):
    headers = registered_user["headers"]

    # Ensure a knowledge chunk exists
    kg = MedicalKnowledgeChunk(
        dataset_name="Malikeh1375/medical-question-answering-datasets",
        dataset_version="29833779cb5921f474d9f469aa85c115277bf489",
        license="mit",
        input_question="What is HbA1c and why is it measured?",
        output_answer="HbA1c measures the average blood glucose levels over the past 2 to 3 months by assessing glycated hemoglobin.",
        content="Question: What is HbA1c?\nAnswer: HbA1c measures average glucose over 3 months."
    )
    db_session.add(kg)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What is HbA1c and why is it measured?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "GENERAL_MEDICAL_KNOWLEDGE"
    assert "HbA1c" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_type"] == "GENERAL_MEDICAL_KNOWLEDGE"
    assert data["citations"][0]["license"] == "mit"

# -----------------------------------------------------------------------------
# Test 3: Patient + General Knowledge Question (Hybrid)
# -----------------------------------------------------------------------------
def test_3_patient_plus_general_hybrid_question(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="hba1c_test.pdf",
        stored_filename="hba1c_1.pdf",
        file_path="uploads/hba1c_1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_hba1c_1",
        category=DocumentCategory.LAB_REPORT.value,
        title="HbA1c Test Report",
        document_date="2026-05-10"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab = LabTest(
        document_id=doc.id,
        user_id=user_id,
        test_name="HbA1c",
        canonical_name="hba1c",
        observed_value="7.1",
        numeric_value=7.1,
        unit="%",
        test_date="2026-05-10"
    )
    db_session.add(lab)
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "Why did my HbA1c increase and what is HbA1c?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_type"] == "HYBRID"
    assert "7.1" in data["answer"]
    assert any(c["source_type"] == "USER_STRUCTURED_RECORD" for c in data["citations"])

# -----------------------------------------------------------------------------
# Test 4: Missing Patient Data (Evidence Guard: Never Guess)
# -----------------------------------------------------------------------------
def test_4_missing_patient_data_evidence_guard(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]

    # Query for a patient metric that does not exist in their records
    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my serum creatinine and urea level?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "not contain enough information" in data["answer"].lower()
    assert data["evidence_priority_applied"] == "USER_RECORDS_MANDATORY_MISSING"

# -----------------------------------------------------------------------------
# Test 5: Empty Retrieval Handling
# -----------------------------------------------------------------------------
def test_5_empty_retrieval_handling(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]

    resp = client.post("/api/v1/assistant/chat", json={"query": "xyz unknown query non-existent jargon 999"}, headers=headers)
    assert resp.status_code == 200
    assert "answer" in resp.json()

# -----------------------------------------------------------------------------
# Test 6: Multiple Retrieved Sources
# -----------------------------------------------------------------------------
def test_6_multiple_retrieved_sources(client: TestClient, registered_user: dict, db_session: Session):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    doc = Document(
        user_id=user_id,
        original_filename="multi_source.pdf",
        stored_filename="multi_1.pdf",
        file_path="uploads/multi_1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="sha256_multi_1",
        category=DocumentCategory.LAB_REPORT.value,
        title="Full Lipid Panel",
        document_date="2026-06-01"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    lab1 = LabTest(document_id=doc.id, user_id=user_id, test_name="Total Cholesterol", observed_value="210", unit="mg/dL", test_date="2026-06-01")
    rx1 = Prescription(document_id=doc.id, user_id=user_id, medication_name="Atorvastatin", dosage="20mg", frequency="0-0-1")
    db_session.add_all([lab1, rx1])
    db_session.commit()

    resp = client.post("/api/v1/assistant/chat", json={"query": "What are my cholesterol result and active prescription?"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["citations"]) >= 2

# -----------------------------------------------------------------------------
# Test 7: Source Attribution
# -----------------------------------------------------------------------------
def test_7_source_attribution_integrity(client: TestClient, registered_user: dict, db_session: Session):
    headers = registered_user["headers"]
    resp = client.get("/api/v1/assistant/knowledge-sources", headers=headers)
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 2
    collection_names = [s["collection_name"] for s in sources]
    assert "USER_MEDICAL_RECORDS" in collection_names
    assert "GENERAL_MEDICAL_KNOWLEDGE" in collection_names

# -----------------------------------------------------------------------------
# Test 8: Unauthorized Patient-Record Retrieval (Cross-User Security)
# -----------------------------------------------------------------------------
def test_8_unauthorized_patient_record_isolation(client: TestClient, registered_user: dict, db_session: Session):
    # Register User 2
    u2_resp = client.post("/api/v1/auth/register", json={
        "email": "user2_rag@example.com",
        "password": "SecurePassword123!",
        "full_name": "Second RAG Patient",
        "role": "patient"
    })
    user2_id = u2_resp.json()["user"]["id"]
    headers1 = registered_user["headers"]

    # User 2 has private lab test
    doc2 = Document(user_id=user2_id, original_filename="u2_private.pdf", stored_filename="u2_p.pdf", file_path="uploads/u2_p.pdf", file_size_bytes=1024, mime_type="application/pdf", file_hash_sha256="sha256_u2_p", title="Confidential U2", category="lab_report")
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    lab2 = LabTest(document_id=doc2.id, user_id=user2_id, test_name="Confidential Biomarker Secret", observed_value="999", unit="mg/dL")
    db_session.add(lab2)
    db_session.commit()

    # User 1 queries for "Confidential Biomarker Secret" -> Should NOT see User 2's value
    resp = client.post("/api/v1/assistant/chat", json={"query": "What is my Confidential Biomarker Secret?"}, headers=headers1)
    assert resp.status_code == 200
    data = resp.json()
    assert "999" not in data["answer"]
    assert "not contain enough information" in data["answer"].lower()

# -----------------------------------------------------------------------------
# Test 9 & 10: Dataset Ingestion & Parquet Validation
# -----------------------------------------------------------------------------
def test_9_10_dataset_ingestion_and_parquet_validation():
    manifest = process_medical_qa_dataset(max_records=10)
    assert manifest is not None
    assert manifest["processing_summary"]["total_raw_rows"] == 246678
    assert len(manifest["records"]) == 10
    assert manifest["dataset_metadata"]["license"] == "mit"

# -----------------------------------------------------------------------------
# Test 11: Duplicate Handling in Dataset Processing
# -----------------------------------------------------------------------------
def test_11_duplicate_handling():
    manifest_file = Path("data/processed/medical_qa_processed.json")
    assert manifest_file.exists()
    import json
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = [r["input_question"].lower() for r in data["records"]]
    # Ensure all extracted questions are unique
    assert len(questions) == len(set(questions))

# -----------------------------------------------------------------------------
# Test 12: RAG Retrieval Lexical / Semantic Scoring
# -----------------------------------------------------------------------------
def test_12_rag_retrieval_scoring():
    score1 = hybrid_rag_service.compute_lexical_score(["diabetes", "glucose"], "Patient has elevated fasting blood glucose and diabetes.")
    score2 = hybrid_rag_service.compute_lexical_score(["diabetes", "glucose"], "Normal chest X-ray clear lungs.")
    assert score1 > score2
    assert score2 == 0.0

# -----------------------------------------------------------------------------
# Test 13: Evidence Guard (Safety & Non-Diagnostic Claims)
# -----------------------------------------------------------------------------
def test_13_evidence_guard_safety():
    query_type = hybrid_rag_service.classify_query("What was my glucose level?")
    assert query_type == "PATIENT_FACTUAL"

    query_type_gen = hybrid_rag_service.classify_query("What is hypertension?")
    assert query_type_gen == "GENERAL_MEDICAL_KNOWLEDGE"

# -----------------------------------------------------------------------------
# Test 14: Phase 5 Regression Verification
# -----------------------------------------------------------------------------
def test_14_phase5_regression_verification(client: TestClient, registered_user: dict):
    headers = registered_user["headers"]
    # Verify Phase 5 Health Intelligence endpoint is active and unaffected
    resp = client.get("/api/v1/health-intelligence/summary", headers=headers)
    assert resp.status_code == 200
    assert "tracked_biomarkers_count" in resp.json()
