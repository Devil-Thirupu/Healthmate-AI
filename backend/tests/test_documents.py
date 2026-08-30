import io
import pytest
from backend.app.models.document import DocumentCategory

def test_document_upload_and_integrity(client, registered_user):
    pdf_content = b"%PDF-1.4 Mock Lab Report Content: HbA1c 7.2%, Creatinine 1.1 mg/dL"
    file_tuple = ("blood_test_report.pdf", io.BytesIO(pdf_content), "application/pdf")
    
    data = {
        "title": "Comprehensive Annual Blood Panel",
        "category": DocumentCategory.LAB_REPORT.value,
        "document_date": "2026-08-15",
        "doctor_name": "Dr. S. Ramanathan",
        "clinic_or_lab": "Apollo Diagnostics Chennai"
    }
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data=data,
        headers=registered_user["headers"]
    )
    assert response.status_code == 201
    doc = response.json()
    doc_id = doc["id"]
    assert doc["title"] == "Comprehensive Annual Blood Panel"
    assert doc["category"] == "lab_report"
    assert doc["file_size_bytes"] == len(pdf_content)
    assert len(doc["file_hash_sha256"]) == 64

    # List documents
    list_resp = client.get("/api/v1/documents/", headers=registered_user["headers"])
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)

    # Get details
    detail_resp = client.get(f"/api/v1/documents/{doc_id}", headers=registered_user["headers"])
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["clinic_or_lab"] == "Apollo Diagnostics Chennai"

    # Download document with integrity verification
    download_resp = client.get(f"/api/v1/documents/{doc_id}/download", headers=registered_user["headers"])
    assert download_resp.status_code == 200
    assert download_resp.content == pdf_content

    # Preview document
    preview_resp = client.get(f"/api/v1/documents/{doc_id}/preview", headers=registered_user["headers"])
    assert preview_resp.status_code == 200

    # Update metadata
    update_payload = {"title": "Updated Blood Report Title"}
    update_resp = client.put(f"/api/v1/documents/{doc_id}", json=update_payload, headers=registered_user["headers"])
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Blood Report Title"

    # Delete document
    delete_resp = client.delete(f"/api/v1/documents/{doc_id}", headers=registered_user["headers"])
    assert delete_resp.status_code == 200
    
    # Confirm deletion
    get_after_delete = client.get(f"/api/v1/documents/{doc_id}", headers=registered_user["headers"])
    assert get_after_delete.status_code == 404
