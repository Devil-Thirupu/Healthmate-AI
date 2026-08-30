import io
import pytest
from pathlib import Path
from backend.app.services.ocr_service import ocr_service
from backend.app.services.clinical_extractor import clinical_extractor
from backend.app.models.document import DocumentCategory, OCRStatus

def test_clinical_lab_extraction():
    sample_ocr_text = """
    APOLLO DIAGNOSTICS - CLINICAL BIOCHEMISTRY REPORT
    Patient: Karthik Subramanian | Date: 2026-08-15
    ---------------------------------------------------------
    Test Parameter                  Result     Unit       Reference Range
    ---------------------------------------------------------
    Fasting Blood Sugar (FBS)       135.0      mg/dL      70 - 99 mg/dL
    HbA1c (Glycated Hemoglobin)     7.2        %          4.0 - 5.6 %
    Serum Creatinine                1.1        mg/dL      0.6 - 1.2 mg/dL
    Total Cholesterol               215.0      mg/dL      < 200 mg/dL
    LDL Cholesterol (Bad)           128.0      mg/dL      < 100 mg/dL
    Hemoglobin (Hb)                 14.5       g/dL       12.0 - 16.5 g/dL
    ---------------------------------------------------------
    """
    results = clinical_extractor.extract_lab_tests(sample_ocr_text, document_date="2026-08-15")
    assert len(results) >= 5

    # Check HbA1c
    hba1c = next((r for r in results if r["canonical_name"] == "hba1c"), None)
    assert hba1c is not None
    assert hba1c["numeric_value"] == 7.2
    assert hba1c["flag"] == "high" # > 5.6
    assert "நீரிழிவு" in hba1c["explanation_tamil"]

    # Check Creatinine (normal)
    creat = next((r for r in results if r["canonical_name"] == "creatinine"), None)
    assert creat is not None
    assert creat["numeric_value"] == 1.1
    assert creat["flag"] == "normal"

    # Check Fasting Glucose (high)
    fbs = next((r for r in results if r["canonical_name"] == "glucose_fasting"), None)
    assert fbs is not None
    assert fbs["numeric_value"] == 135.0
    assert fbs["flag"] == "high"

def test_prescription_medication_extraction():
    sample_rx_text = """
    DR. S. RAMANATHAN, MD (General Medicine)
    Apollo Clinics, Chennai
    Date: 2026-08-10
    
    Rx:
    1. Tab Metformin 500mg - 1-0-1 (Twice daily) After food x 30 days
    2. Tab Atorvastatin 10mg - 0-0-1 (Night) After dinner x 30 days
    3. Tab Pantoprazole 40mg - 1-0-0 (Morning) Before food x 14 days
    """
    rx_results = clinical_extractor.extract_prescriptions(sample_rx_text, doctor_name="Dr. S. Ramanathan", document_date="2026-08-10")
    assert len(rx_results) >= 3

    metformin = next((m for m in rx_results if m["medication_name"] == "Metformin"), None)
    assert metformin is not None
    assert "500" in metformin["dosage"]
    assert "Twice daily" in metformin["frequency"]
    assert "After" in metformin["timing_instructions"]
    assert "சர்க்கரை" in metformin["instructions_tamil"]

    pantoprazole = next((m for m in rx_results if m["medication_name"] == "Pantoprazole"), None)
    assert pantoprazole is not None
    assert "Before" in pantoprazole["timing_instructions"]

def test_radiology_archival_non_diagnostic():
    # Test that imaging documents receive clear archival non-diagnostic compliance tags
    res = ocr_service.process_document("nonexistent_chest_xray.png", category="imaging")
    assert "RADIOLOGICAL IMAGING RECORD" in res["full_text"]
    assert "NOT FOR AUTOMATED CLINICAL DIAGNOSIS" in res["full_text"]
    assert res["confidence_score"] == 100.0

def test_rag_chunk_creation():
    pages = [
        {"page_number": 1, "text": "Medical Summary: Patient has a history of hypertension.\n\nActive medications include Telmisartan 40mg."},
        {"page_number": 2, "text": "Lab test observations from August 2026 show well-controlled renal panel."}
    ]
    chunks = clinical_extractor.create_rag_chunks(document_id=1, user_id=1, pages_data=pages)
    assert len(chunks) >= 3
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert len(chunks[0]["content"]) > 0

def test_upload_with_ocr_and_corrections(client, registered_user):
    # Upload a text-based medical report
    report_content = b"""%PDF-1.4
    BLOOD TEST REPORT
    Patient: Karthik
    Fasting Blood Sugar: 125 mg/dL
    HbA1c: 6.8 %
    Tab Metformin 500mg - BD PC x 30 days
    """
    file_tuple = ("clinical_test_doc.pdf", io.BytesIO(report_content), "application/pdf")
    
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={"title": "Diagnostic Report 2026", "category": "lab_report", "doctor_name": "Dr. Raman"},
        headers=registered_user["headers"]
    )
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["ocr_status"] == OCRStatus.COMPLETED.value

    # Check detail endpoint returns extracted lab tests and prescriptions
    detail_resp = client.get(f"/api/v1/documents/{doc_id}", headers=registered_user["headers"])
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "ocr_raw_text" in detail
    assert len(detail["lab_tests"]) >= 1
    assert len(detail["prescriptions"]) >= 1

    # Perform Human-in-the-Loop Manual Correction
    correction_payload = {
        "title": "Corrected Blood Panel Title",
        "lab_tests": [
            {
                "test_name": "HbA1c (Glycated Hemoglobin)",
                "canonical_name": "hba1c",
                "observed_value": "6.7",
                "numeric_value": 6.7,
                "unit": "%",
                "flag": "high",
                "reference_range_text": "4.0 - 5.6 %"
            }
        ]
    }
    correction_resp = client.put(
        f"/api/v1/documents/{doc_id}/corrections",
        json=correction_payload,
        headers=registered_user["headers"]
    )
    assert correction_resp.status_code == 200
    corrected = correction_resp.json()
    assert corrected["title"] == "Corrected Blood Panel Title"
    assert corrected["has_manual_corrections"] is True
    assert len(corrected["lab_tests"]) == 1
    assert corrected["lab_tests"][0]["numeric_value"] == 6.7
    assert corrected["lab_tests"][0]["is_manual_edited"] is True
