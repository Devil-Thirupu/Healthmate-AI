import io
import pytest

def test_patient_controlled_sharing(client, registered_user):
    # Upload a document first
    pdf_content = b"%PDF-1.4 Mock Lab Document for Sharing"
    file_tuple = ("rx_to_share.pdf", io.BytesIO(pdf_content), "application/pdf")
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={"title": "Prescription for Second Opinion", "category": "prescription"},
        headers=registered_user["headers"]
    )
    doc_id = upload_resp.json()["id"]

    # 1. Create a PIN-protected share link (valid for 48 hours)
    share_payload = {
        "title": "Prescription Consultation",
        "recipient_name": "Dr. V. Natarajan",
        "document_ids": [doc_id],
        "is_pin_protected": True,
        "pin": "7890",
        "duration_hours": 48,
        "max_access_count": 5,
        "allow_download": True,
        "allow_ai_summary": True
    }
    create_resp = client.post("/api/v1/sharing/create", json=share_payload, headers=registered_user["headers"])
    assert create_resp.status_code == 201
    share_data = create_resp.json()
    token = share_data["token"]
    link_id = share_data["id"]
    assert share_data["is_pin_protected"] is True

    # 2. Check public status of the link without PIN (should return metadata + pin required flag)
    public_status = client.get(f"/api/v1/sharing/public/{token}")
    assert public_status.status_code == 200
    meta = public_status.json()
    assert meta["is_valid"] is True
    assert meta["is_pin_required"] is True
    assert meta["recipient_name"] == "Dr. V. Natarajan"

    # 3. Access with wrong PIN (should fail 401)
    wrong_pin_resp = client.post(f"/api/v1/sharing/public/{token}/access", json={"pin": "0000"})
    assert wrong_pin_resp.status_code == 401

    # 4. Access with correct PIN (should succeed 200 and return documents)
    correct_pin_resp = client.post(f"/api/v1/sharing/public/{token}/access", json={"pin": "7890"})
    assert correct_pin_resp.status_code == 200
    access_data = correct_pin_resp.json()
    assert access_data["patient_name"] == "Karthik Subramanian"
    assert len(access_data["documents"]) >= 1

    # 5. Revoke link as patient
    revoke_resp = client.delete(f"/api/v1/sharing/{link_id}", headers=registered_user["headers"])
    assert revoke_resp.status_code == 200

    # 6. Check that revoked link is no longer accessible
    revoked_status = client.get(f"/api/v1/sharing/public/{token}")
    assert revoked_status.json()["is_valid"] is False
