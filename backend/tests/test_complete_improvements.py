import io
import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.clinical import LabTest, Prescription
from backend.app.models.sharing import SharedLink
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.core.security import get_password_hash, create_access_token

def test_supabase_health_diagnostic_endpoint(client):
    """Verifies that the Supabase diagnostic endpoint returns safe structured status without exposing keys."""
    resp = client.get("/api/v1/health/supabase")
    assert resp.status_code == 200
    data = resp.json()
    assert "supabase_url_configured" in data
    assert "database_engine" in data
    assert "database_connectivity" in data
    assert data["database_connectivity"] == "connected"
    assert "supabase_storage_status" in data
    assert "is_production_ready" in data
    # Ensure no secret keys or passwords exposed
    assert "service_role" not in str(data).lower()
    assert "password" not in str(data).lower()

def test_token_auth_via_query_param(client, registered_user, db_session):
    """Verifies that ?token= query parameter authenticates requests for iframe and direct download."""
    # Upload a test file
    pdf_content = b"%PDF-1.4 Mock Clinical Report for Preview Test"
    file_tuple = ("test_preview.pdf", io.BytesIO(pdf_content), "application/pdf")
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={"title": "Preview Blood Test", "category": "lab_report"},
        headers=registered_user["headers"]
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    token = registered_user["token"]

    # 1. Preview using query param ?token=
    preview_resp = client.get(f"/api/v1/documents/{doc_id}/preview?token={token}")
    assert preview_resp.status_code in [200, 302]

    # 2. Download using query param ?token=
    download_resp = client.get(f"/api/v1/documents/{doc_id}/download?token={token}")
    assert download_resp.status_code in [200, 302]

    # 3. Preview without any token must fail 401
    unauth_resp = client.get(f"/api/v1/documents/{doc_id}/preview")
    assert unauth_resp.status_code == 401

def test_shared_document_preview_and_download(client, registered_user, db_session):
    """Verifies public sharing document preview and download endpoints with token authorization."""
    # Upload a document
    pdf_content = b"%PDF-1.4 Shared Medical Document Content"
    file_tuple = ("shared_doc.pdf", io.BytesIO(pdf_content), "application/pdf")
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={"title": "Doctor Consultation Report", "category": "lab_report"},
        headers=registered_user["headers"]
    )
    doc_id = upload_resp.json()["id"]

    # Create share link
    share_payload = {
        "title": "Public Consultation Share",
        "recipient_name": "Dr. Ramesh",
        "document_ids": [doc_id],
        "is_pin_protected": False,
        "duration_hours": 24,
        "allow_download": True
    }
    create_resp = client.post("/api/v1/sharing/create", json=share_payload, headers=registered_user["headers"])
    assert create_resp.status_code == 201
    token = create_resp.json()["token"]

    # Preview shared document
    share_preview_resp = client.get(f"/api/v1/sharing/public/{token}/document/{doc_id}/preview")
    assert share_preview_resp.status_code in [200, 302]

    # Download shared document
    share_dl_resp = client.get(f"/api/v1/sharing/public/{token}/document/{doc_id}/download")
    assert share_dl_resp.status_code in [200, 302]

    # Unauthorized doc_id for this share link must fail 403
    unauth_doc_resp = client.get(f"/api/v1/sharing/public/{token}/document/99999/preview")
    assert unauth_doc_resp.status_code == 403

def test_nutrition_lab_report_recommendations(client, registered_user, db_session):
    """Verifies that nutrition analysis links low/flagged lab biomarkers to USDA foods."""
    user_id = registered_user["user"]["id"]

    # Add a mock low hemoglobin lab test
    low_hb = LabTest(
        user_id=user_id,
        test_name="Hemoglobin (Hb)",
        canonical_name="Hemoglobin (Hb)",
        observed_value="10.2",
        numeric_value=10.2,
        unit="g/dL",
        reference_range_min=12.0,
        reference_range_max=16.5,
        reference_range_text="12.0 - 16.5 g/dL",
        flag="low",
        test_date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    db_session.add(low_hb)
    db_session.commit()

    resp = client.get("/api/v1/nutrition/report-recommendations", headers=registered_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert "insights" in data
    assert data["total_insights"] >= 1
    hb_insight = next((i for i in data["insights"] if "hemoglobin" in i["canonical_name"].lower()), None)
    assert hb_insight is not None
    assert "Iron" in hb_insight["relevant_nutrient"]
    assert len(hb_insight["suggested_foods"]) > 0
    first_food = hb_insight["suggested_foods"][0]
    assert "food_name" in first_food
    assert "calories_kcal" in first_food
    assert "nutrient_amount" in first_food
    assert "disclaimer" in hb_insight

def test_cross_user_isolation(client, registered_user, db_session):
    """Ensures that User A cannot access or retrieve User B's documents, records, or RAG data."""
    # Create User B
    user_b = User(
        email="user_b@healthmate.ai",
        hashed_password=get_password_hash("SecretPassword123!"),
        full_name="User Bravo",
        is_active=True
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    token_b = create_access_token(subject=user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads a document
    pdf_content = b"%PDF-1.4 User A Private Document"
    file_tuple = ("private_a.pdf", io.BytesIO(pdf_content), "application/pdf")
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": file_tuple},
        data={"title": "Confidential User A Lab", "category": "lab_report"},
        headers=registered_user["headers"]
    )
    doc_a_id = upload_resp.json()["id"]

    # User B tries to view/download User A's document -> must be 404
    b_get_resp = client.get(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert b_get_resp.status_code == 404

    b_preview_resp = client.get(f"/api/v1/documents/{doc_a_id}/preview", headers=headers_b)
    assert b_preview_resp.status_code == 404
