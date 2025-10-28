"""
Pytest configuration and shared fixtures for FHIR Analytics Platform tests.

This module provides common fixtures used across all test modules.
"""

import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash
from main import app


# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """
    Create a fresh database for each test function.
    
    Yields:
        Session: SQLAlchemy database session
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """
    Create a test client with database override.
    
    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }


@pytest.fixture
def test_admin_data():
    """Sample test admin user data."""
    return {
        "username": "testadmin",
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Test Admin",
        "role": "admin",
        "is_active": True
    }


@pytest.fixture
def create_test_user(test_db, test_user_data):
    """Factory fixture to create test users."""
    from app.models.user import User
    
    def _create_user(**kwargs):
        user_data = test_user_data.copy()
        user_data.update(kwargs)
        
        password = user_data.pop("password")
        user = User(
            **user_data,
            hashed_password=get_password_hash(password)
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def authenticated_client(client, create_test_user, test_user_data):
    """
    Create an authenticated test client.
    
    Returns:
        tuple: (TestClient, user_token, user_object)
    """
    # Create user
    user = create_test_user()
    
    # Login to get token
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Set auth header
    client.headers = {"Authorization": f"Bearer {token}"}
    
    return client, token, user


@pytest.fixture
def admin_client(client, create_test_user, test_admin_data):
    """
    Create an authenticated admin test client.
    
    Returns:
        tuple: (TestClient, admin_token, admin_user)
    """
    # Create admin user
    admin = create_test_user(**test_admin_data)
    
    # Login to get token
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_admin_data["username"],
            "password": test_admin_data["password"]
        }
    )
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Set auth header
    client.headers = {"Authorization": f"Bearer {token}"}
    
    return client, token, admin


@pytest.fixture
def sample_patient_data():
    """Sample FHIR patient data."""
    return {
        "fhir_id": "patient-123",
        "identifier": "MRN123456",
        "family_name": "Smith",
        "given_name": "John",
        "gender": "male",
        "birth_date": "1980-01-01"
    }


@pytest.fixture
def sample_condition_data():
    """Sample FHIR condition data."""
    return {
        "fhir_id": "condition-123",
        "patient_id": 1,
        "code": {"coding": [{"system": "SNOMED-CT", "code": "38341003", "display": "Hypertension"}]},
        "code_text": "Hypertension",
        "clinical_status": "active",
        "onset_datetime": "2023-01-01T00:00:00"
    }


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client."""
    mock = mocker.Mock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = 1
    return mock


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32-chars"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # Cleanup
    os.environ.pop("ENVIRONMENT", None)

