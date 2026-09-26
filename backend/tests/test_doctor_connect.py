"""
Doctor Connect — Backend Test Suite
=====================================
Tests for: doctors, connections, appointments, access grants, security boundaries.
Run: python -m pytest backend/tests/test_doctor_connect.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.doctor import (
    Doctor, PatientDoctorConnection, Appointment, DoctorAccessGrant,
    ConnectionStatus, AppointmentStatus
)
from backend.app.core.security import get_password_hash, create_access_token

# ─── Test DB setup ─────────────────────────────────────────────────────────

SQLALCHEMY_TEST_URL = "sqlite:///./test_doctor_connect.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def patient_user(db):
    user = User(
        email="patient_dc@test.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test Patient",
        role="patient",
        date_of_birth="1990-05-15",
        blood_group="O+",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def patient_token(patient_user):
    return create_access_token(subject=str(patient_user.id))


@pytest.fixture(scope="module")
def other_user(db):
    user = User(
        email="other_dc@test.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Other User",
        role="patient",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def other_token(other_user):
    return create_access_token(subject=str(other_user.id))


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ─── 1. DOCTOR CREATE ─────────────────────────────────────────────────────

class TestDoctorCreate:
    def test_create_doctor_success(self, client, patient_token):
        res = client.post("/api/v1/doctors/", json={
            "name": "Dr. Ramachandran",
            "specialization": "Cardiologist",
            "hospital_or_clinic": "Apollo Hospitals",
            "phone_number": "+91 9876543210",
            "consultation_type": "in_person",
            "available_days": "Mon,Wed,Fri",
            "available_time": "09:00-17:00",
        }, headers=auth(patient_token))
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Dr. Ramachandran"
        assert data["specialization"] == "Cardiologist"
        assert "id" in data

    def test_create_doctor_missing_name(self, client, patient_token):
        res = client.post("/api/v1/doctors/", json={
            "specialization": "Cardiologist",
        }, headers=auth(patient_token))
        assert res.status_code == 422  # Validation error

    def test_create_doctor_unauthenticated(self, client):
        res = client.post("/api/v1/doctors/", json={"name": "Dr. X"})
        assert res.status_code == 401


# ─── 2. DOCTOR UPDATE ────────────────────────────────────────────────────

class TestDoctorUpdate:
    def test_update_doctor(self, client, patient_token, db, patient_user):
        # Create a fresh doctor for this test
        doctor = Doctor(name="Dr. Update Test", created_by_user_id=patient_user.id)
        db.add(doctor); db.commit(); db.refresh(doctor)

        res = client.put(f"/api/v1/doctors/{doctor.id}", json={
            "phone_number": "+91 9999999999",
            "notes": "Updated notes",
        }, headers=auth(patient_token))
        assert res.status_code == 200
        assert res.json()["notes"] == "Updated notes"

    def test_update_other_users_doctor_fails(self, client, other_token, db, patient_user):
        doctor = Doctor(name="Dr. Private", created_by_user_id=patient_user.id)
        db.add(doctor); db.commit(); db.refresh(doctor)

        res = client.put(f"/api/v1/doctors/{doctor.id}", json={"notes": "hack"},
                         headers=auth(other_token))
        assert res.status_code == 404  # Not found for other user


# ─── 3. DOCTOR CONNECT ────────────────────────────────────────────────────

class TestDoctorConnect:
    @pytest.fixture(autouse=True)
    def doctor(self, db, patient_user):
        doc = Doctor(name="Dr. Connect Test", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)
        self._doctor = doc
        return doc

    def test_connect_doctor(self, client, patient_token):
        res = client.post("/api/v1/doctors/connections/request", json={
            "doctor_id": self._doctor.id,
            "patient_note": "Hello doctor",
        }, headers=auth(patient_token))
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "pending"
        assert data["doctor_id"] == self._doctor.id

    def test_duplicate_connection_rejected(self, client, patient_token):
        # Create initial pending connection
        client.post("/api/v1/doctors/connections/request", json={
            "doctor_id": self._doctor.id,
        }, headers=auth(patient_token))
        # A pending connection already exists for this doctor -> 409 Conflict
        res = client.post("/api/v1/doctors/connections/request", json={
            "doctor_id": self._doctor.id,
        }, headers=auth(patient_token))
        assert res.status_code == 409  # Conflict

    def test_list_connections(self, client, patient_token):
        res = client.get("/api/v1/doctors/connections", headers=auth(patient_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) >= 1


# ─── 4. REJECT CONNECTION ─────────────────────────────────────────────────

class TestConnectionReject:
    def test_cancel_pending_connection(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. Cancel Test", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            status=ConnectionStatus.PENDING.value
        )
        db.add(conn); db.commit(); db.refresh(conn)

        res = client.patch(f"/api/v1/doctors/connections/{conn.id}",
                           json={"status": "cancelled"}, headers=auth(patient_token))
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"

    def test_invalid_transition_fails(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. BadTransition", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit(); db.refresh(conn)

        # accepted → cancelled is not allowed (only disconnected is)
        res = client.patch(f"/api/v1/doctors/connections/{conn.id}",
                           json={"status": "cancelled"}, headers=auth(patient_token))
        assert res.status_code == 422


# ─── 5. DISCONNECT ────────────────────────────────────────────────────────

class TestDisconnect:
    def test_disconnect_accepted_connection(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. Disconnect Test", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit(); db.refresh(conn)

        res = client.patch(f"/api/v1/doctors/connections/{conn.id}",
                           json={"status": "disconnected"}, headers=auth(patient_token))
        assert res.status_code == 200
        assert res.json()["status"] == "disconnected"


# ─── 6. REQUEST APPOINTMENT ──────────────────────────────────────────────

class TestRequestAppointment:
    @pytest.fixture(autouse=True)
    def doctor_and_conn(self, db, patient_user):
        doc = Doctor(name="Dr. Appt Test", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)
        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit(); db.refresh(conn)
        self._doctor = doc
        self._conn = conn

    def test_request_appointment(self, client, patient_token):
        res = client.post("/api/v1/doctors/appointments", json={
            "doctor_id": self._doctor.id,
            "requested_date": "2026-12-01",
            "requested_time": "10:00",
            "consultation_type": "in_person",
            "reason": "Follow-up",
            "patient_note": "Please check blood reports",
        }, headers=auth(patient_token))
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "pending"  # NEVER confirmed until doctor accepts
        assert data["requested_date"] == "2026-12-01"

    def test_appointment_status_is_pending_not_confirmed(self, client, patient_token):
        res = client.post("/api/v1/doctors/appointments", json={
            "doctor_id": self._doctor.id,
            "requested_date": "2026-12-15",
        }, headers=auth(patient_token))
        assert res.status_code == 201
        # Critical safety check: must never return 'confirmed'
        assert res.json()["status"] != "confirmed"
        assert res.json()["status"] == "pending"

    def test_request_appointment_unauthenticated(self, client):
        res = client.post("/api/v1/doctors/appointments", json={
            "doctor_id": 999, "requested_date": "2026-12-01"
        })
        assert res.status_code == 401


# ─── 7. ACCEPT / REJECT APPOINTMENT (future doctor endpoint) ─────────────

class TestAppointmentAcceptReject:
    def test_list_appointments(self, client, patient_token):
        res = client.get("/api/v1/doctors/appointments", headers=auth(patient_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_cancel_appointment(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. CancelAppt", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        appt = Appointment(
            patient_id=patient_user.id, doctor_id=doc.id,
            requested_date="2026-11-01", status=AppointmentStatus.PENDING.value
        )
        db.add(appt); db.commit(); db.refresh(appt)

        res = client.patch(f"/api/v1/doctors/appointments/{appt.id}",
                           json={"status": "cancelled"}, headers=auth(patient_token))
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"

    def test_patient_cannot_accept_own_appointment(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. SelfAccept", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        appt = Appointment(
            patient_id=patient_user.id, doctor_id=doc.id,
            requested_date="2026-11-10", status=AppointmentStatus.PENDING.value
        )
        db.add(appt); db.commit(); db.refresh(appt)

        res = client.patch(f"/api/v1/doctors/appointments/{appt.id}",
                           json={"status": "accepted"}, headers=auth(patient_token))
        # Only doctor can accept — patients get 422
        assert res.status_code == 422


# ─── 8. RESCHEDULE APPOINTMENT ───────────────────────────────────────────

class TestRescheduleAppointment:
    def test_patient_can_update_date(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. Reschedule", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        appt = Appointment(
            patient_id=patient_user.id, doctor_id=doc.id,
            requested_date="2026-11-20", status=AppointmentStatus.PENDING.value
        )
        db.add(appt); db.commit(); db.refresh(appt)

        res = client.patch(f"/api/v1/doctors/appointments/{appt.id}",
                           json={"requested_date": "2026-11-25"},
                           headers=auth(patient_token))
        # No status change = allowed (just updating date)
        assert res.status_code == 200
        assert res.json()["requested_date"] == "2026-11-25"


# ─── 9. CREATE SHARE (ACCESS GRANT) ─────────────────────────────────────

class TestCreateShare:
    @pytest.fixture(autouse=True)
    def connected_doctor(self, db, patient_user):
        doc = Doctor(name="Dr. Share Test", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)
        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit(); db.refresh(conn)
        self._doctor = doc

    def test_create_share_with_granular_permissions(self, client, patient_token):
        res = client.post("/api/v1/doctors/access-grants", json={
            "doctor_id": self._doctor.id,
            "share_blood_type": True,
            "share_lab_reports": True,
            "share_current_medications": False,
            "share_prescriptions": False,
            "allow_download": False,
            "duration_hours": 168,
        }, headers=auth(patient_token))
        assert res.status_code == 201
        data = res.json()
        assert data["share_blood_type"] is True
        assert data["share_lab_reports"] is True
        assert data["share_current_medications"] is False  # Not enabled
        assert "grant_token" in data
        assert data["is_active"] is True

    def test_create_share_without_connection_fails(self, client, other_token, db, other_user):
        # other_user has no connection to self._doctor
        res = client.post("/api/v1/doctors/access-grants", json={
            "doctor_id": self._doctor.id,
            "share_blood_type": True,
            "duration_hours": 24,
        }, headers=auth(other_token))
        assert res.status_code in [403, 404]  # Forbidden or not found

    def test_create_share_unauthenticated(self, client):
        res = client.post("/api/v1/doctors/access-grants", json={
            "doctor_id": 1, "duration_hours": 24
        })
        assert res.status_code == 401


# ─── 10. EXPIRED SHARE ───────────────────────────────────────────────────

class TestExpiredShare:
    def test_expired_grant_returns_invalid(self, client, db, patient_user):
        doc = Doctor(name="Dr. Expired", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit()

        # Expired grant
        expired = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            connection_id=conn.id,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # already expired
            is_active=True,
        )
        db.add(expired); db.commit(); db.refresh(expired)

        res = client.get(f"/api/v1/doctors/access-grants/view/{expired.grant_token}")
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid"] is False
        assert data["is_expired"] is True


# ─── 11. REVOKED SHARE ───────────────────────────────────────────────────

class TestRevokedShare:
    def test_revoke_grant(self, client, patient_token, db, patient_user):
        doc = Doctor(name="Dr. Revoke Test", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit()

        grant = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            connection_id=conn.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
            is_active=True,
        )
        db.add(grant); db.commit(); db.refresh(grant)

        # Revoke
        res = client.delete(f"/api/v1/doctors/access-grants/{grant.id}",
                            headers=auth(patient_token))
        assert res.status_code == 200

        # View should now be invalid
        view_res = client.get(f"/api/v1/doctors/access-grants/view/{grant.grant_token}")
        assert view_res.status_code == 200
        assert view_res.json()["is_valid"] is False
        assert view_res.json()["is_revoked"] is True


# ─── 12. UNAUTHORIZED DOCTOR ACCESS ─────────────────────────────────────

class TestUnauthorizedDoctorAccess:
    def test_other_user_cannot_see_my_doctors(self, client, other_token, db, patient_user):
        doc = Doctor(name="Dr. Private Doc", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        # other_token should get 404 (filtered by created_by_user_id)
        res = client.get(f"/api/v1/doctors/{doc.id}", headers=auth(other_token))
        assert res.status_code == 404

    def test_other_user_cannot_revoke_my_grant(self, client, other_token, db, patient_user):
        doc = Doctor(name="Dr. Protect Grant", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        grant = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True,
        )
        db.add(grant); db.commit(); db.refresh(grant)

        res = client.delete(f"/api/v1/doctors/access-grants/{grant.id}",
                            headers=auth(other_token))
        assert res.status_code == 404  # Not visible to other user


# ─── 13. AUTHORIZED DOCTOR ACCESS ────────────────────────────────────────

class TestAuthorizedDoctorAccess:
    def test_valid_grant_token_returns_data(self, client, db, patient_user):
        doc = Doctor(name="Dr. Authorized", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit()

        grant = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            connection_id=conn.id,
            share_blood_type=True,
            share_age=True,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True,
        )
        db.add(grant); db.commit(); db.refresh(grant)

        res = client.get(f"/api/v1/doctors/access-grants/view/{grant.grant_token}")
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid"] is True
        assert data["patient_name"] == patient_user.full_name
        # Blood type shared
        assert data["patient_blood_type"] == patient_user.blood_group or data["patient_blood_type"] == "Not provided"

    def test_valid_grant_does_not_expose_unshared_fields(self, client, db, patient_user):
        doc = Doctor(name="Dr. Selective", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        grant = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            share_blood_type=False,  # NOT shared
            share_lab_reports=False,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True,
        )
        db.add(grant); db.commit(); db.refresh(grant)

        res = client.get(f"/api/v1/doctors/access-grants/view/{grant.grant_token}")
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid"] is True
        # Blood type NOT shared — should be None or "Not provided"
        assert data.get("patient_blood_type") in [None, "Not provided"]
        assert data["lab_reports"] == []


# ─── 14. DOWNLOAD PERMISSION ─────────────────────────────────────────────

class TestDownloadPermission:
    def test_download_flag_reflected_in_grant(self, client, db, patient_user):
        doc = Doctor(name="Dr. Download", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        grant = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            allow_download=True,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True,
        )
        db.add(grant); db.commit(); db.refresh(grant)

        res = client.get(f"/api/v1/doctors/access-grants/view/{grant.grant_token}")
        assert res.status_code == 200
        assert res.json()["allow_download"] is True

    def test_no_download_without_flag(self, client, db, patient_user):
        doc = Doctor(name="Dr. NoDownload", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        grant = DoctorAccessGrant(
            patient_id=patient_user.id,
            doctor_id=doc.id,
            allow_download=False,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_active=True,
        )
        db.add(grant); db.commit(); db.refresh(grant)

        res = client.get(f"/api/v1/doctors/access-grants/view/{grant.grant_token}")
        assert res.status_code == 200
        assert res.json()["allow_download"] is False


# ─── 15. AUDIT LOGGING ───────────────────────────────────────────────────

class TestAuditLogging:
    def test_audit_log_created_after_doctor_create(self, client, patient_token, db):
        from backend.app.models.audit import AuditLog
        initial_count = db.query(AuditLog).filter(AuditLog.action == "DOCTOR_CREATED").count()

        client.post("/api/v1/doctors/", json={"name": "Dr. Audit Test"},
                    headers=auth(patient_token))

        new_count = db.query(AuditLog).filter(AuditLog.action == "DOCTOR_CREATED").count()
        assert new_count == initial_count + 1

    def test_audit_log_on_share_create(self, client, patient_token, db, patient_user):
        from backend.app.models.audit import AuditLog
        doc = Doctor(name="Dr. AuditShare", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)
        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id,
            status=ConnectionStatus.ACCEPTED.value
        )
        db.add(conn); db.commit()

        initial = db.query(AuditLog).filter(AuditLog.action == "SHARE_CREATED").count()

        client.post("/api/v1/doctors/access-grants", json={
            "doctor_id": doc.id,
            "share_blood_type": True,
            "duration_hours": 24,
        }, headers=auth(patient_token))

        final = db.query(AuditLog).filter(AuditLog.action == "SHARE_CREATED").count()
        assert final == initial + 1

    def test_audit_log_on_appointment_request(self, client, patient_token, db, patient_user):
        from backend.app.models.audit import AuditLog
        doc = Doctor(name="Dr. AuditAppt", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        initial = db.query(AuditLog).filter(AuditLog.action == "APPOINTMENT_REQUESTED").count()

        client.post("/api/v1/doctors/appointments", json={
            "doctor_id": doc.id,
            "requested_date": "2026-12-20",
        }, headers=auth(patient_token))

        final = db.query(AuditLog).filter(AuditLog.action == "APPOINTMENT_REQUESTED").count()
        assert final == initial + 1


# ─── 16. RLS / SECURITY BOUNDARIES ─────────────────────────────────────

class TestSecurityBoundaries:
    def test_appointment_not_visible_to_other_user(self, client, other_token, db, patient_user):
        doc = Doctor(name="Dr. SecAppt", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        appt = Appointment(
            patient_id=patient_user.id, doctor_id=doc.id,
            requested_date="2026-12-30", status="pending"
        )
        db.add(appt); db.commit(); db.refresh(appt)

        res = client.get(f"/api/v1/doctors/appointments/{appt.id}", headers=auth(other_token))
        assert res.status_code == 404

    def test_connection_not_visible_to_other_user(self, client, other_token, db, patient_user):
        doc = Doctor(name="Dr. SecConn", created_by_user_id=patient_user.id)
        db.add(doc); db.commit(); db.refresh(doc)

        conn = PatientDoctorConnection(
            patient_id=patient_user.id, doctor_id=doc.id, status="pending"
        )
        db.add(conn); db.commit(); db.refresh(conn)

        res = client.patch(f"/api/v1/doctors/connections/{conn.id}",
                           json={"status": "cancelled"}, headers=auth(other_token))
        assert res.status_code == 404

    def test_invalid_grant_token_returns_404(self, client):
        res = client.get("/api/v1/doctors/access-grants/view/totally_invalid_token_xyz")
        assert res.status_code == 404
