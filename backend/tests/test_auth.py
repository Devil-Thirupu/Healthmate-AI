import pytest
from backend.app.core.security import verify_password, get_password_hash

def test_password_hashing():
    raw_pwd = "MySecretHealthPassword#99"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_register_user(client):
    payload = {
        "email": "dr.priya@apollo.org",
        "password": "DoctorSecure2026!",
        "full_name": "Dr. Priya Sundaram",
        "role": "doctor",
        "language_preference": "en"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "dr.priya@apollo.org"
    assert data["user"]["full_name"] == "Dr. Priya Sundaram"
    assert data["user"]["role"] == "doctor"

def test_register_duplicate_email(client, registered_user):
    payload = {
        "email": "testpatient@example.com",
        "password": "AnotherPassword123!",
        "full_name": "Duplicate User"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success(client, registered_user):
    payload = {
        "email": "testpatient@example.com",
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testpatient@example.com"

def test_login_failure(client):
    payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

def test_get_current_user_profile(client, registered_user):
    response = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testpatient@example.com"
    assert data["blood_group"] == "O+"

def test_update_profile(client, registered_user):
    update_data = {
        "allergies": "Penicillin, Sulfa drugs",
        "chronic_conditions": "Hypertension, Pre-diabetes",
        "emergency_contact": "+91 98400 12345 (Spouse)"
    }
    response = client.put("/api/v1/auth/me", json=update_data, headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["allergies"] == "Penicillin, Sulfa drugs"
    assert data["chronic_conditions"] == "Hypertension, Pre-diabetes"

def test_change_password(client, registered_user):
    payload = {
        "current_password": "SecurePassword123!",
        "new_password": "BrandNewPassword999!"
    }
    response = client.put("/api/v1/auth/change-password", json=payload, headers=registered_user["headers"])
    assert response.status_code == 200
    
    # Try logging in with old password (should fail)
    old_login = client.post("/api/v1/auth/login", json={"email": "testpatient@example.com", "password": "SecurePassword123!"})
    assert old_login.status_code == 401

    # Try logging in with new password (should succeed)
    new_login = client.post("/api/v1/auth/login", json={"email": "testpatient@example.com", "password": "BrandNewPassword999!"})
    assert new_login.status_code == 200
