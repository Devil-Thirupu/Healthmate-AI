import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.rag import RAGChunk, MedicalKnowledgeChunk
from backend.app.core.security import create_access_token, get_password_hash

def get_or_create_users(db_session: Session):
    u1 = db_session.query(User).filter(User.email == "patient_rag_1@example.com").first()
    if not u1:
        u1 = User(
            email="patient_rag_1@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Alice Walker",
            language_preference="en",
            is_active=True
        )
        db_session.add(u1)

    u2 = db_session.query(User).filter(User.email == "patient_rag_2@example.com").first()
    if not u2:
        u2 = User(
            email="patient_rag_2@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Bob Miller",
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

def seed_assistant_rag_data(db_session: Session, u1: User, u2: User):
    # Ensure Medical Knowledge chunk exists
    med_qa = db_session.query(MedicalKnowledgeChunk).filter(MedicalKnowledgeChunk.input_question.ilike("%glucose%")).first()
    if not med_qa:
        med_qa = MedicalKnowledgeChunk(
            input_question="What is glucose and what is its normal range?",
            output_answer="Glucose is the primary simple sugar providing energy to cells. Normal fasting plasma glucose is typically between 70 and 99 mg/dL.",
            content="Q: What is glucose and what is its normal range?\nA: Glucose is the primary simple sugar providing energy to cells. Normal fasting plasma glucose is typically between 70 and 99 mg/dL.",
            dataset_name="Medical QA Reference (MIT)",
            license="MIT"
        )
        db_session.add(med_qa)
        db_session.commit()

    # User 1: Report 1 (Older - Jan 2026)
    doc1 = Document(
        user_id=u1.id,
        original_filename="jan_report.pdf",
        stored_filename="jan_report_u1.pdf",
        file_path="uploads/jan_report_u1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_jan_u1",
        category="lab_report",
        title="Jan Metabolic Panel",
        document_date="2026-01-15",
        ocr_status="completed",
        ocr_raw_text="Fasting Blood Glucose: 100 mg/dL."
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
        observed_value="100",
        unit="mg/dL",
        flag="normal",
        reference_range_text="70-99 mg/dL",
        test_date="2026-01-15"
    )
    db_session.add(t1)

    # User 1: Report 2 (Newer - March 2026)
    doc2 = Document(
        user_id=u1.id,
        original_filename="mar_report.pdf",
        stored_filename="mar_report_u1.pdf",
        file_path="uploads/mar_report_u1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash_sha256="hash_mar_u1",
        category="lab_report",
        title="March Blood Report",
        document_date="2026-03-20",
        ocr_status="completed",
        ocr_raw_text="Fasting Blood Glucose: 105 mg/dL. Total Hemoglobin: 13.5 g/dL."
    )
    db_session.add(doc2)
    db_session.commit()
    db_session.refresh(doc2)

    t2 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="Fasting Blood Glucose",
        canonical_name="glucose",
        test_category="metabolic",
        observed_value="105",
        unit="mg/dL",
        flag="high",
        reference_range_text="70-99 mg/dL",
        test_date="2026-03-20"
    )
    t3 = LabTest(
        document_id=doc2.id,
        user_id=u1.id,
        test_name="Hemoglobin",
        canonical_name="hemoglobin",
        test_category="hematology",
        observed_value="13.5",
        unit="g/dL",
        flag="normal",
        reference_range_text="12.0-15.5 g/dL",
        test_date="2026-03-20"
    )
    db_session.add_all([t2, t3])

    # User 1: Prescription
    doc3 = Document(
        user_id=u1.id,
        original_filename="prescription_march.pdf",
        stored_filename="rx_march_u1.pdf",
        file_path="uploads/rx_march_u1.pdf",
        file_size_bytes=512,
        mime_type="application/pdf",
        file_hash_sha256="hash_rx_u1",
        category="prescription",
        title="Prescription March",
        document_date="2026-03-20",
        ocr_status="completed",
        ocr_raw_text="Amoxicillin 500 mg, twice daily for 7 days."
    )
    db_session.add(doc3)
    db_session.commit()
    db_session.refresh(doc3)

    rx1 = Prescription(
        document_id=doc3.id,
        user_id=u1.id,
        medication_name="Amoxicillin",
        dosage="500 mg",
        frequency="Twice daily",
        timing_instructions="After food",
        duration="7 days",
        prescribed_date="2026-03-20"
    )
    db_session.add(rx1)

    # User 1: RAG Chunk
    chunk1 = RAGChunk(
        user_id=u1.id,
        document_id=doc2.id,
        chunk_index=0,
        content="March Blood Report Page 1: Fasting Blood Glucose measured 105 mg/dL on March 20, 2026.",
        page_number=1
    )
    db_session.add(chunk1)

    # User 2: Isolated Data
    doc_u2 = Document(
        user_id=u2.id,
        original_filename="u2_secret.pdf",
        stored_filename="u2_secret.pdf",
        file_path="uploads/u2_secret.pdf",
        file_size_bytes=512,
        mime_type="application/pdf",
        file_hash_sha256="hash_u2_secret",
        category="lab_report",
        title="User 2 Secret Lipid Report",
        document_date="2026-03-25",
        ocr_status="completed",
        ocr_raw_text="Total Cholesterol: 240 mg/dL."
    )
    db_session.add(doc_u2)
    db_session.commit()
    db_session.refresh(doc_u2)

    t_u2 = LabTest(
        document_id=doc_u2.id,
        user_id=u2.id,
        test_name="Total Cholesterol",
        canonical_name="cholesterol",
        test_category="lipid",
        observed_value="240",
        unit="mg/dL",
        flag="high",
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


def test_1_latest_values_query_returns_actual_records(client: TestClient, db_session: Session):
    """Verifies that 'What are my latest values?' returns actual stored values (105 mg/dL, 13.5 g/dL) and NOT general knowledge."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post("/api/v1/assistant/chat", json={"query": "What are my latest values?", "language": "en"}, headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "SUPPORTED"
    assert "105" in data["answer"]
    assert "13.5" in data["answer"]
    assert "Glucose" in data["answer"]
    assert "Hemoglobin" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["source_type"] == "USER_STRUCTURED_RECORD"


def test_2_month_date_filtering_glucose_in_march(client: TestClient, db_session: Session):
    """Verifies that 'What was my glucose in March?' returns March glucose (105 mg/dL)."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post("/api/v1/assistant/chat", json={"query": "What was my glucose in March?", "language": "en"}, headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "SUPPORTED"
    assert "105" in data["answer"]
    assert "March" in data["citations"][0]["source_name"] or "2026-03-20" in data["answer"]


def test_3_missing_month_records_returns_insufficient(client: TestClient, db_session: Session):
    """Verifies that querying for a month without records (e.g. 'What was my cholesterol in January?') returns INSUFFICIENT evidence."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post("/api/v1/assistant/chat", json={"query": "What was my cholesterol in January?", "language": "en"}, headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "INSUFFICIENT"
    assert "not contain enough information" in data["answer"].lower() or "missing" in data["answer"].lower()


def test_4_prescription_query_returns_actual_medications(client: TestClient, db_session: Session):
    """Verifies that 'What medicines are listed in my prescription?' returns Amoxicillin 500 mg."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post("/api/v1/assistant/chat", json={"query": "What medicines are listed in my prescription?", "language": "en"}, headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "SUPPORTED"
    assert "Amoxicillin" in data["answer"]
    assert "500 mg" in data["answer"]
    assert "Twice daily" in data["answer"]


def test_5_report_content_query(client: TestClient, db_session: Session):
    """Verifies that 'What is in my latest report?' retrieves the user's latest document and chunks."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post("/api/v1/assistant/chat", json={"query": "What is in my latest report?", "language": "en"}, headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "SUPPORTED"
    assert len(data["citations"]) >= 1


def test_6_pure_general_medical_question(client: TestClient, db_session: Session):
    """Verifies that 'What is glucose?' retrieves General Medical Knowledge without referencing patient records."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post("/api/v1/assistant/chat", json={"query": "What is glucose?", "language": "en"}, headers=h1)
    assert res.status_code == 200
    data = res.json()
    assert data["query_type"] == "GENERAL_MEDICAL_KNOWLEDGE"
    assert data["evidence_status"] == "SUPPORTED"
    assert "glucose" in data["answer"].lower()


def test_7_hybrid_question_patient_plus_general(client: TestClient, db_session: Session):
    """Verifies that hybrid queries provide patient values and general context with no personal causality claims."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    res = client.post(
        "/api/v1/assistant/chat",
        json={"query": "My glucose changed from 100 to 105. What does that mean?", "language": "en"},
        headers=h1
    )
    assert res.status_code == 200
    data = res.json()
    assert "105" in data["answer"]
    assert "cannot establish personal causality" in data["answer"].lower() or "informational" in data["answer"].lower() or "disclaimer" in data["answer"].lower()


def test_8_cross_user_isolation(client: TestClient, db_session: Session):
    """User 1 must never see User 2's confidential cholesterol record."""
    u1, u2, h1, h2 = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    # User 1 asks about cholesterol (User 1 has no cholesterol record)
    res1 = client.post("/api/v1/assistant/chat", json={"query": "What is my cholesterol?", "language": "en"}, headers=h1)
    assert res1.status_code == 200
    assert res1.json()["evidence_status"] == "INSUFFICIENT"
    assert "240" not in res1.json()["answer"]

    # User 2 asks about cholesterol (User 2 has 240 mg/dL)
    res2 = client.post("/api/v1/assistant/chat", json={"query": "What is my cholesterol?", "language": "en"}, headers=h2)
    assert res2.status_code == 200
    assert res2.json()["evidence_status"] == "SUPPORTED"
    assert "240" in res2.json()["answer"]


def test_9_trilingual_metric_preservation(client: TestClient, db_session: Session):
    """Verifies that Tamil and Tanglish chat responses preserve exact clinical values (105 mg/dL)."""
    u1, u2, h1, _ = get_or_create_users(db_session)
    seed_assistant_rag_data(db_session, u1, u2)

    # Tamil
    res_ta = client.post("/api/v1/assistant/chat", json={"query": "What are my latest values?", "language": "ta"}, headers=h1)
    assert res_ta.status_code == 200
    assert "105" in res_ta.json()["answer"]
    assert "mg/dL" in res_ta.json()["answer"]

    # Tanglish
    res_tang = client.post("/api/v1/assistant/chat", json={"query": "What are my latest values?", "language": "tanglish"}, headers=h1)
    assert res_tang.status_code == 200
    assert "105" in res_tang.json()["answer"]
    assert "mg/dL" in res_tang.json()["answer"]
