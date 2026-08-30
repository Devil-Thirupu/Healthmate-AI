import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["SECRET_KEY"] = "test-secret-key-healthmate-ai-super-secure"

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.core.security import create_access_token
import backend.app.models

# Use in-memory SQLite database for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def registered_user(client):
    user_payload = {
        "email": "testpatient@example.com",
        "password": "SecurePassword123!",
        "full_name": "Karthik Subramanian",
        "role": "patient",
        "date_of_birth": "1988-05-14",
        "gender": "Male",
        "blood_group": "O+",
        "language_preference": "ta"
    }
    response = client.post("/api/v1/auth/register", json=user_payload)
    data = response.json()
    return {
        "user": data["user"],
        "token": data["access_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "raw_payload": user_payload
    }
