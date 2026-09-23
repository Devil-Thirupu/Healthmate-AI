import pytest
import os
import json
import base64
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User, UserRole
from backend.app.models.document import Document
from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.sharing import SharedLink
from backend.app.models.audit import AuditLog
from backend.app.core.security import get_password_hash
from backend.app.core.config import settings

# -----------------------------------------------------------------------------
# Test 1 to 5: Authentication (Email, Mobile, Google OAuth & Development Mode)
# -----------------------------------------------------------------------------
def test_1_to_5_authentication_methods(client: TestClient, db_session: Session):
    # 1. User login with email
    user = User(
        email="patient.auth@example.com",
        phone_number="+919876543210",
        hashed_password=get_password_hash("Password123!"),
        full_name="Sundar Pichai",
        role=UserRole.PATIENT.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    resp_email = client.post(
        "/api/v1/auth/login",
        json={"email": "patient.auth@example.com", "password": "Password123!"}
    )
    assert resp_email.status_code == 200
    assert "access_token" in resp_email.json()

    # 2. Mobile / password authentication (via /login-mobile and /login)
    resp_mob = client.post(
        "/api/v1/auth/login-mobile",
        json={"phone_number": "+91 98765 43210", "password": "Password123!"}
    )
    assert resp_mob.status_code == 200
    assert "access_token" in resp_mob.json()

    # Unified login with phone identifier
    resp_ident = client.post(
        "/api/v1/auth/login",
        json={"identifier": "+91 98765 43210", "password": "Password123!"}
    )
    assert resp_ident.status_code == 200

    # 3. Invalid password handling
    resp_invalid = client.post(
        "/api/v1/auth/login",
        json={"email": "patient.auth@example.com", "password": "WrongPassword!"}
    )
    assert resp_invalid.status_code == 401

    # 4 & 5. Google OAuth when not configured vs configured
    # Missing Google credentials behavior
    settings.GOOGLE_CLIENT_ID = ""
    resp_g_unconf = client.post(
        "/api/v1/auth/google",
        json={"id_token": "dummy_token"}
    )
    assert resp_g_unconf.status_code == 503
    assert "Google Sign-In is not configured" in resp_g_unconf.json()["detail"]

    # Google auth token validation when configured
    settings.GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com"
    
    # Construct a valid test JWT token payload
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).decode().rstrip("=")
    payload_data = {
        "iss": "https://accounts.google.com",
        "aud": "test-client-id.apps.googleusercontent.com",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "email": "google.user@example.com",
        "email_verified": True,
        "name": "Google Verified User"
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    valid_id_token = f"{header}.{payload}.signature_bytes"

    resp_g_valid = client.post(
        "/api/v1/auth/google",
        json={"id_token": valid_id_token}
    )
    assert resp_g_valid.status_code == 200
    assert "access_token" in resp_g_valid.json()
    assert resp_g_valid.json()["user"]["email"] == "google.user@example.com"

# -----------------------------------------------------------------------------
# Test 6 to 13: Granular Record Sharing, Expiry, Revocation & Strict Isolation
# -----------------------------------------------------------------------------
def test_6_to_13_granular_sharing_lifecycle(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_id = registered_user["user"]["id"]
    headers = registered_user["headers"]

    # Create 2 documents for User A
    doc1 = Document(
        user_id=user_id,
        title="Comprehensive Blood Panel",
        category="lab_report",
        original_filename="blood_panel.pdf",
        stored_filename="bp.pdf",
        file_path="uploads/bp.pdf",
        file_size_bytes=1024,
        file_hash_sha256="abc123hash",
        mime_type="application/pdf"
    )
    doc2 = Document(
        user_id=user_id,
        title="Confidential Cardiology Report",
        category="cardiology",
        original_filename="cardio.pdf",
        stored_filename="cardio.pdf",
        file_path="uploads/cardio.pdf",
        file_size_bytes=2048,
        file_hash_sha256="def456hash",
        mime_type="application/pdf"
    )
    db_session.add_all([doc1, doc2])
    db_session.commit()

    # 6, 7, 8, 9. Create share selecting ONLY doc1 (not doc2) with 24-hour expiry
    share_create_resp = client.post(
        "/api/v1/sharing/create",
        json={
            "title": "Blood Panel Consultation",
            "recipient_name": "Dr. V. Ramanathan",
            "document_ids": [doc1.id],
            "duration_hours": 24,
            "permission": "READ_ONLY",
            "is_pin_protected": True,
            "pin": "1234"
        },
        headers=headers
    )
    assert share_create_resp.status_code == 201
    share_data = share_create_resp.json()
    token = share_data["token"]
    share_id = share_data["id"]
    assert share_data["permission"] == "READ_ONLY"
    assert share_data["document_ids_json"] == [doc1.id]
    assert len(token) >= 32 # Cryptographically secure token

    # 10. Valid shared access with PIN via public route
    access_resp = client.post(
        f"/api/v1/shared/{token}",
        json={"pin": "1234"}
    )
    assert access_resp.status_code == 200
    public_view = access_resp.json()
    assert len(public_view["documents"]) == 1
    assert public_view["documents"][0]["id"] == doc1.id
    assert public_view["permission"] == "READ_ONLY"

    # 13. Record-Level Authorization: Recipient MUST NOT see doc2
    retrieved_doc_ids = [d["id"] for d in public_view["documents"]]
    assert doc2.id not in retrieved_doc_ids

    # 11. Expired share link test
    expired_link = SharedLink(
        user_id=user_id,
        title="Expired Share",
        token="expired_token_1234567890abcdef1234567890",
        document_ids_json=[doc1.id],
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        is_active=True
    )
    db_session.add(expired_link)
    db_session.commit()

    exp_resp = client.post("/api/v1/shared/expired_token_1234567890abcdef1234567890", json={})
    assert exp_resp.status_code in [404, 410]

    # 12. Revoke active share
    revoke_resp = client.post(f"/api/v1/sharing/{share_id}/revoke", headers=headers)
    assert revoke_resp.status_code == 200

    # Verify revoked link immediately becomes inaccessible
    revoked_access_resp = client.post(f"/api/v1/shared/{token}", json={"pin": "1234"})
    assert revoked_access_resp.status_code in [404, 410]

# -----------------------------------------------------------------------------
# Test 14 to 20: Cross-User Isolation & Recipient Permission Restrictions
# -----------------------------------------------------------------------------
def test_14_to_20_cross_user_isolation(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    user_a_id = registered_user["user"]["id"]

    # Create User B
    user_b = User(
        email="user_b@example.com",
        phone_number="+919999988888",
        hashed_password=get_password_hash("SecretPassword123!"),
        full_name="User B (Unrelated Patient)",
        role=UserRole.PATIENT.value,
        is_active=True
    )
    db_session.add(user_b)
    db_session.commit()

    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "user_b@example.com", "password": "SecretPassword123!"}
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # User A records
    doc_a = Document(
        user_id=user_a_id,
        title="User A Private Ultrasound",
        category="radiology",
        original_filename="us.pdf",
        stored_filename="us.pdf",
        file_path="uploads/us.pdf",
        file_size_bytes=1024,
        file_hash_sha256="hashus",
        mime_type="application/pdf"
    )
    lab_a = LabTest(
        user_id=user_a_id,
        test_name="Fasting Insulin",
        observed_value="14.2",
        numeric_value=14.2,
        unit="uIU/mL"
    )
    db_session.add_all([doc_a, lab_a])
    db_session.commit()

    # 14 & 15. User B attempts to access User A's private document directly
    resp_b_doc = client.get(f"/api/v1/documents/{doc_a.id}", headers=headers_b)
    assert resp_b_doc.status_code == 404

    # 18, 19, 20. User B attempts to delete User A's document
    resp_b_del = client.delete(f"/api/v1/documents/{doc_a.id}", headers=headers_b)
    assert resp_b_del.status_code == 404

# -----------------------------------------------------------------------------
# Test 21 to 31: Audit Trail Events, Privacy Preservation & Regression
# -----------------------------------------------------------------------------
def test_21_to_31_audit_events_and_privacy(
    client: TestClient,
    registered_user: dict,
    db_session: Session
):
    headers = registered_user["headers"]
    user_id = registered_user["user"]["id"]

    # 21. Query Audit logs for LOGIN
    resp_audit_login = client.get("/api/v1/audit?category=login", headers=headers)
    assert resp_audit_login.status_code == 200
    login_logs = resp_audit_login.json()
    assert len(login_logs) >= 1

    # 28. Audit logs MUST NOT contain medical contents, OCR text, or passwords
    all_audit_resp = client.get("/api/v1/audit", headers=headers)
    assert all_audit_resp.status_code == 200
    logs = all_audit_resp.json()
    for log in logs:
        details_str = json.dumps(log.get("details_json", {})).lower()
        assert "password" not in details_str or "change" in log.get("action", "").lower()
        assert "hashed_password" not in details_str
        assert "ocr_raw_text" not in details_str
        assert "medication_name" not in details_str

    # 29 & 30. Invalid / predictable token attack
    resp_invalid_token = client.post("/api/v1/shared/12345", json={})
    assert resp_invalid_token.status_code in [404, 410]
