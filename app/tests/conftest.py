"""
Test configuration and fixtures for DreamBig Real Estate Platform
"""
import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
from unittest.mock import Mock, patch

from app.main import app
from app.db.session import get_db, Base
from app.core.security import create_access_token
from app.db import crud
from app.db.models import User, Property, Investment, PropertyBooking
from app.utils.i18n import translation_manager

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Test user data for creating users."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "phone": "+1234567890",
        "firebase_uid": "test_firebase_uid_123",
        "role": "tenant",
        "is_active": True,
        "kyc_verified": False
    }

@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    user = crud.create_user(db_session, test_user_data)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user in the database."""
    admin_data = {
        "email": "admin@example.com",
        "name": "Admin User",
        "phone": "+1234567891",
        "firebase_uid": "admin_firebase_uid_123",
        "role": "admin",
        "is_active": True,
        "kyc_verified": True
    }
    user = crud.create_user(db_session, admin_data)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_property_owner(db_session):
    """Create a test property owner user."""
    owner_data = {
        "email": "owner@example.com",
        "name": "Property Owner",
        "phone": "+1234567892",
        "firebase_uid": "owner_firebase_uid_123",
        "role": "owner",
        "is_active": True,
        "kyc_verified": True
    }
    user = crud.create_user(db_session, owner_data)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_property_data():
    """Test property data for creating properties."""
    return {
        "title": "Test Property",
        "description": "A beautiful test property",
        "price": 5000000.0,
        "bhk": 3,
        "area": 1200.0,
        "property_type": "apartment",
        "furnishing": "furnished",
        "address": "123 Test Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "status": "available",
        "is_verified": True
    }

@pytest.fixture
def test_property(db_session, test_property_owner, test_property_data):
    """Create a test property in the database."""
    property_data = test_property_data.copy()
    property_data["owner_id"] = test_property_owner.id
    
    property_obj = Property(**property_data)
    db_session.add(property_obj)
    db_session.commit()
    db_session.refresh(property_obj)
    return property_obj

@pytest.fixture
def test_investment_data():
    """Test investment data for creating investments."""
    return {
        "title": "Test Investment",
        "amount": 1000000.0,
        "expected_roi": 12.5,
        "risk_level": "medium",
        "investment_type": "property",
        "duration_months": 24,
        "description": "A test investment opportunity",
        "location": "Mumbai",
        "status": "active"
    }

@pytest.fixture
def test_investment(db_session, test_user, test_property, test_investment_data):
    """Create a test investment in the database."""
    investment_data = test_investment_data.copy()
    investment_data["investor_id"] = test_user.id
    investment_data["property_id"] = test_property.id
    
    investment = Investment(**investment_data)
    db_session.add(investment)
    db_session.commit()
    db_session.refresh(investment)
    return investment

@pytest.fixture
def test_booking_data():
    """Test booking data for creating property bookings."""
    from datetime import datetime, timedelta
    return {
        "booking_type": "viewing",
        "preferred_date": datetime.utcnow() + timedelta(days=1),
        "preferred_time": "10:00",
        "duration_minutes": 60,
        "notes": "Test booking",
        "contact_name": "Test User",
        "contact_phone": "+1234567890",
        "contact_email": "test@example.com"
    }

@pytest.fixture
def test_booking(db_session, test_user, test_property, test_booking_data):
    """Create a test property booking in the database."""
    booking_data = test_booking_data.copy()
    booking_data["user_id"] = test_user.id
    booking_data["property_id"] = test_property.id
    
    booking = PropertyBooking(**booking_data)
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    access_token = create_access_token(
        data={"sub": test_user.firebase_uid, "user_id": test_user.id}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers(test_admin_user):
    """Create authentication headers for admin user."""
    access_token = create_access_token(
        data={"sub": test_admin_user.firebase_uid, "user_id": test_admin_user.id}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def owner_auth_headers(test_property_owner):
    """Create authentication headers for property owner."""
    access_token = create_access_token(
        data={"sub": test_property_owner.firebase_uid, "user_id": test_property_owner.id}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def mock_firebase():
    """Mock Firebase authentication for testing."""
    with patch('app.core.security.verify_firebase_token') as mock_verify:
        mock_verify.return_value = {
            "uid": "test_firebase_uid_123",
            "email": "test@example.com",
            "name": "Test User"
        }
        yield mock_verify

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    with patch('app.core.ai_services.ai_service') as mock_ai:
        mock_ai.get_property_recommendations.return_value = [
            {"property_id": 1, "score": 0.95, "reason": "Perfect match"},
            {"property_id": 2, "score": 0.87, "reason": "Good location"}
        ]
        mock_ai.analyze_property_description.return_value = {
            "sentiment": "positive",
            "key_features": ["spacious", "modern", "well-located"],
            "suggested_price_range": {"min": 4500000, "max": 5500000}
        }
        yield mock_ai

@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    with patch('app.utils.notifications.send_notification') as mock_notify:
        mock_notify.return_value = True
        yield mock_notify

@pytest.fixture
def mock_sms_service():
    """Mock SMS service for testing."""
    with patch('app.utils.sms.send_sms') as mock_sms:
        mock_sms.return_value = {"success": True, "message_id": "test_msg_123"}
        yield mock_sms

@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    with patch('app.utils.email.send_email') as mock_email:
        mock_email.return_value = True
        yield mock_email

@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for file uploads during testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the upload directory
        with patch('app.core.document_manager.document_manager.upload_dir', temp_dir):
            yield temp_dir

@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing uploads."""
    import io
    from PIL import Image
    
    # Create a simple test image
    image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return ("test_image.jpg", img_bytes, "image/jpeg")

@pytest.fixture
def sample_video_file():
    """Create a sample video file for testing uploads."""
    import io
    
    # Create a mock video file
    video_content = b"fake video content for testing"
    video_bytes = io.BytesIO(video_content)
    
    return ("test_video.mp4", video_bytes, "video/mp4")

@pytest.fixture
def mock_business_rules():
    """Mock business rules engine for testing."""
    with patch('app.utils.business_rules.BusinessRulesEngine') as mock_engine:
        mock_instance = Mock()
        mock_instance.calculate_property_valuation.return_value = Mock(
            estimated_value=5200000.0,
            confidence_score=0.85,
            valuation_method="cma",
            comparable_properties=[],
            market_factors={},
            last_updated=None
        )
        mock_instance.validate_booking_request.return_value = {
            "is_valid": True,
            "requires_approval": False,
            "violations": [],
            "recommendations": [],
            "pricing_adjustments": {}
        }
        mock_engine.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_legal_compliance():
    """Mock legal compliance manager for testing."""
    with patch('app.utils.legal_compliance.LegalComplianceManager') as mock_manager:
        mock_instance = Mock()
        mock_instance.record_consent.return_value = True
        mock_instance.get_user_consents.return_value = {
            "terms_of_service": {
                "consent_given": True,
                "consent_date": "2024-01-01T00:00:00Z",
                "consent_version": "1.0"
            }
        }
        mock_instance.generate_data_export.return_value = {
            "success": True,
            "export_data": {"user_data": "test_data"}
        }
        mock_manager.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_translation_manager():
    """Mock translation manager for testing."""
    with patch.object(translation_manager, 'get_translation') as mock_translate:
        mock_translate.return_value = "Translated text"
        yield mock_translate

# Performance testing fixtures

@pytest.fixture
def performance_test_data():
    """Generate data for performance testing."""
    return {
        "users_count": 100,
        "properties_count": 500,
        "bookings_count": 200,
        "concurrent_requests": 10
    }

# Integration test fixtures

@pytest.fixture
def integration_test_setup(db_session):
    """Set up data for integration tests."""
    # Create multiple users
    users = []
    for i in range(5):
        user_data = {
            "email": f"user{i}@example.com",
            "name": f"User {i}",
            "phone": f"+123456789{i}",
            "firebase_uid": f"firebase_uid_{i}",
            "role": "tenant" if i < 3 else "owner",
            "is_active": True,
            "kyc_verified": i % 2 == 0
        }
        user = crud.create_user(db_session, user_data)
        users.append(user)
    
    # Create multiple properties
    properties = []
    for i in range(10):
        property_data = {
            "title": f"Property {i}",
            "description": f"Description for property {i}",
            "price": 1000000.0 + (i * 500000),
            "bhk": (i % 4) + 1,
            "area": 800.0 + (i * 100),
            "property_type": ["apartment", "house", "villa"][i % 3],
            "furnishing": ["furnished", "semi_furnished", "unfurnished"][i % 3],
            "address": f"{i+1} Test Street",
            "city": ["Mumbai", "Delhi", "Bangalore"][i % 3],
            "state": ["Maharashtra", "Delhi", "Karnataka"][i % 3],
            "pincode": f"40000{i}",
            "latitude": 19.0760 + (i * 0.01),
            "longitude": 72.8777 + (i * 0.01),
            "status": "available",
            "is_verified": True,
            "owner_id": users[3 + (i % 2)].id  # Assign to owner users
        }
        property_obj = Property(**property_data)
        db_session.add(property_obj)
        properties.append(property_obj)
    
    db_session.commit()
    
    return {
        "users": users,
        "properties": properties
    }

# Utility functions for tests

def assert_response_success(response, expected_status=200):
    """Assert that a response is successful."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"

def assert_response_error(response, expected_status=400):
    """Assert that a response contains an error."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"

def assert_valid_property_response(property_data):
    """Assert that property response data is valid."""
    required_fields = ["id", "title", "price", "bhk", "area", "property_type", "city"]
    for field in required_fields:
        assert field in property_data, f"Missing required field: {field}"
    
    assert isinstance(property_data["price"], (int, float))
    assert property_data["price"] > 0
    assert isinstance(property_data["bhk"], int)
    assert property_data["bhk"] > 0

def assert_valid_user_response(user_data):
    """Assert that user response data is valid."""
    required_fields = ["id", "email", "name", "role"]
    for field in required_fields:
        assert field in user_data, f"Missing required field: {field}"
    
    assert "@" in user_data["email"]
    assert user_data["role"] in ["tenant", "owner", "service_provider", "investor", "admin"]
