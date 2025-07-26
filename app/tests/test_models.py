"""
Unit tests for database models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    User, Property, Investment, PropertyBooking, RentalApplication, 
    PurchaseOffer, UserConsent, AuditLog, LegalDocument,
    UserRole, PropertyType, PropertyStatus, BookingType, BookingStatus
)


class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            name="Test User",
            phone="+1234567890",
            firebase_uid="test_firebase_uid",
            role=UserRole.TENANT
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == UserRole.TENANT
        assert user.is_active is True
        assert user.kyc_verified is False
        assert user.created_at is not None
    
    def test_user_email_unique(self, db_session):
        """Test that user email must be unique."""
        user1 = User(
            email="test@example.com",
            name="User 1",
            firebase_uid="uid1",
            role=UserRole.TENANT
        )
        user2 = User(
            email="test@example.com",
            name="User 2",
            firebase_uid="uid2",
            role=UserRole.OWNER
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_firebase_uid_unique(self, db_session):
        """Test that Firebase UID must be unique."""
        user1 = User(
            email="user1@example.com",
            name="User 1",
            firebase_uid="same_uid",
            role=UserRole.TENANT
        )
        user2 = User(
            email="user2@example.com",
            name="User 2",
            firebase_uid="same_uid",
            role=UserRole.OWNER
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_roles(self, db_session):
        """Test different user roles."""
        roles = [UserRole.TENANT, UserRole.OWNER, UserRole.SERVICE_PROVIDER, 
                UserRole.INVESTOR, UserRole.ADMIN]
        
        for i, role in enumerate(roles):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                firebase_uid=f"uid_{i}",
                role=role
            )
            db_session.add(user)
        
        db_session.commit()
        
        users = db_session.query(User).all()
        assert len(users) == len(roles)
        
        for user, expected_role in zip(users, roles):
            assert user.role == expected_role


class TestPropertyModel:
    """Test Property model functionality."""
    
    def test_create_property(self, db_session, test_property_owner):
        """Test creating a property."""
        property_obj = Property(
            title="Test Property",
            description="A test property",
            price=5000000.0,
            bhk=3,
            area=1200.0,
            property_type=PropertyType.APARTMENT,
            address="123 Test Street",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            owner_id=test_property_owner.id
        )
        db_session.add(property_obj)
        db_session.commit()
        
        assert property_obj.id is not None
        assert property_obj.title == "Test Property"
        assert property_obj.price == 5000000.0
        assert property_obj.property_type == PropertyType.APARTMENT
        assert property_obj.status == PropertyStatus.AVAILABLE
        assert property_obj.is_verified is False
        assert property_obj.created_at is not None
        assert property_obj.owner_id == test_property_owner.id
    
    def test_property_owner_relationship(self, db_session, test_property_owner):
        """Test property-owner relationship."""
        property_obj = Property(
            title="Test Property",
            price=5000000.0,
            bhk=2,
            area=1000.0,
            property_type=PropertyType.HOUSE,
            city="Delhi",
            owner_id=test_property_owner.id
        )
        db_session.add(property_obj)
        db_session.commit()
        
        # Test forward relationship
        assert property_obj.owner == test_property_owner
        
        # Test backward relationship
        assert property_obj in test_property_owner.properties
    
    def test_property_types(self, db_session, test_property_owner):
        """Test different property types."""
        property_types = [PropertyType.APARTMENT, PropertyType.HOUSE, 
                         PropertyType.VILLA, PropertyType.PLOT, PropertyType.COMMERCIAL]
        
        for i, prop_type in enumerate(property_types):
            property_obj = Property(
                title=f"Property {i}",
                price=1000000.0 + i * 500000,
                bhk=2 + i,
                area=800.0 + i * 200,
                property_type=prop_type,
                city="Mumbai",
                owner_id=test_property_owner.id
            )
            db_session.add(property_obj)
        
        db_session.commit()
        
        properties = db_session.query(Property).all()
        assert len(properties) == len(property_types)
        
        for prop, expected_type in zip(properties, property_types):
            assert prop.property_type == expected_type


class TestInvestmentModel:
    """Test Investment model functionality."""
    
    def test_create_investment(self, db_session, test_user, test_property):
        """Test creating an investment."""
        investment = Investment(
            title="Test Investment",
            amount=1000000.0,
            expected_roi=12.5,
            risk_level="medium",
            investment_type="property",
            duration_months=24,
            description="A test investment",
            location="Mumbai",
            investor_id=test_user.id,
            property_id=test_property.id
        )
        db_session.add(investment)
        db_session.commit()
        
        assert investment.id is not None
        assert investment.title == "Test Investment"
        assert investment.amount == 1000000.0
        assert investment.expected_roi == 12.5
        assert investment.status == "active"
        assert investment.investor_id == test_user.id
        assert investment.property_id == test_property.id
    
    def test_investment_relationships(self, db_session, test_user, test_property):
        """Test investment relationships."""
        investment = Investment(
            title="Test Investment",
            amount=500000.0,
            expected_roi=10.0,
            risk_level="low",
            investment_type="property",
            duration_months=12,
            investor_id=test_user.id,
            property_id=test_property.id
        )
        db_session.add(investment)
        db_session.commit()
        
        # Test relationships
        assert investment.investor == test_user
        assert investment.property == test_property
        assert investment in test_user.investments
        assert investment in test_property.investments


class TestBookingModels:
    """Test booking system models."""
    
    def test_create_property_booking(self, db_session, test_user, test_property):
        """Test creating a property booking."""
        booking_date = datetime.utcnow() + timedelta(days=1)
        
        booking = PropertyBooking(
            booking_type=BookingType.VIEWING,
            property_id=test_property.id,
            user_id=test_user.id,
            preferred_date=booking_date,
            preferred_time="10:00",
            duration_minutes=60,
            contact_name="Test User",
            contact_phone="+1234567890",
            contact_email="test@example.com"
        )
        db_session.add(booking)
        db_session.commit()
        
        assert booking.id is not None
        assert booking.booking_type == BookingType.VIEWING
        assert booking.status == BookingStatus.PENDING
        assert booking.preferred_date == booking_date
        assert booking.property_id == test_property.id
        assert booking.user_id == test_user.id
    
    def test_create_rental_application(self, db_session, test_user, test_property):
        """Test creating a rental application."""
        move_in_date = datetime.utcnow() + timedelta(days=30)
        
        application = RentalApplication(
            property_id=test_property.id,
            applicant_id=test_user.id,
            desired_move_in_date=move_in_date,
            lease_duration_months=12,
            offered_rent=50000.0,
            security_deposit=100000.0,
            employment_status="employed",
            employer_name="Test Company",
            monthly_income=80000.0,
            background_check_consent=True
        )
        db_session.add(application)
        db_session.commit()
        
        assert application.id is not None
        assert application.offered_rent == 50000.0
        assert application.lease_duration_months == 12
        assert application.background_check_consent is True
        assert application.property_id == test_property.id
        assert application.applicant_id == test_user.id
    
    def test_create_purchase_offer(self, db_session, test_user, test_property):
        """Test creating a purchase offer."""
        closing_date = datetime.utcnow() + timedelta(days=60)
        
        offer = PurchaseOffer(
            property_id=test_property.id,
            buyer_id=test_user.id,
            offered_price=4800000.0,
            financing_type="mortgage",
            down_payment=960000.0,
            loan_amount=3840000.0,
            closing_date=closing_date,
            earnest_money=100000.0
        )
        db_session.add(offer)
        db_session.commit()
        
        assert offer.id is not None
        assert offer.offered_price == 4800000.0
        assert offer.financing_type == "mortgage"
        assert offer.down_payment == 960000.0
        assert offer.property_id == test_property.id
        assert offer.buyer_id == test_user.id


class TestLegalComplianceModels:
    """Test legal compliance models."""
    
    def test_create_user_consent(self, db_session, test_user):
        """Test creating user consent record."""
        consent = UserConsent(
            user_id=test_user.id,
            consent_type="terms_of_service",
            consent_given=True,
            consent_version="1.0",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            consent_text="I agree to the terms of service"
        )
        db_session.add(consent)
        db_session.commit()
        
        assert consent.id is not None
        assert consent.consent_type == "terms_of_service"
        assert consent.consent_given is True
        assert consent.consent_version == "1.0"
        assert consent.user_id == test_user.id
        assert consent.consent_date is not None
    
    def test_create_audit_log(self, db_session, test_user):
        """Test creating audit log entry."""
        audit_log = AuditLog(
            user_id=test_user.id,
            event_type="login",
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            session_id="test_session_123",
            details={"login_method": "email", "success": True}
        )
        db_session.add(audit_log)
        db_session.commit()
        
        assert audit_log.id is not None
        assert audit_log.event_type == "login"
        assert audit_log.user_id == test_user.id
        assert audit_log.details["login_method"] == "email"
        assert audit_log.event_timestamp is not None
        assert audit_log.archived is False
    
    def test_create_legal_document(self, db_session, test_admin_user):
        """Test creating legal document."""
        effective_date = datetime.utcnow()
        
        document = LegalDocument(
            document_type="terms_of_service",
            version="1.0",
            title="Terms of Service",
            content="These are the terms of service...",
            effective_date=effective_date,
            created_by=test_admin_user.id,
            is_active=True
        )
        db_session.add(document)
        db_session.commit()
        
        assert document.id is not None
        assert document.document_type == "terms_of_service"
        assert document.version == "1.0"
        assert document.is_active is True
        assert document.created_by == test_admin_user.id
        assert document.effective_date == effective_date


class TestModelRelationships:
    """Test complex model relationships."""
    
    def test_user_property_relationship(self, db_session, test_property_owner):
        """Test user can own multiple properties."""
        properties = []
        for i in range(3):
            property_obj = Property(
                title=f"Property {i}",
                price=1000000.0 + i * 500000,
                bhk=2 + i,
                area=800.0 + i * 200,
                property_type=PropertyType.APARTMENT,
                city="Mumbai",
                owner_id=test_property_owner.id
            )
            properties.append(property_obj)
            db_session.add(property_obj)
        
        db_session.commit()
        
        # Test that user has all properties
        assert len(test_property_owner.properties) == 3
        for prop in properties:
            assert prop in test_property_owner.properties
    
    def test_property_booking_relationships(self, db_session, test_user, test_property):
        """Test property can have multiple bookings."""
        bookings = []
        for i in range(3):
            booking_date = datetime.utcnow() + timedelta(days=i+1)
            booking = PropertyBooking(
                booking_type=BookingType.VIEWING,
                property_id=test_property.id,
                user_id=test_user.id,
                preferred_date=booking_date,
                preferred_time=f"{10+i}:00",
                duration_minutes=60
            )
            bookings.append(booking)
            db_session.add(booking)
        
        db_session.commit()
        
        # Test relationships
        assert len(test_property.property_bookings) == 3
        assert len(test_user.property_bookings) == 3
        
        for booking in bookings:
            assert booking in test_property.property_bookings
            assert booking in test_user.property_bookings
    
    def test_cascade_delete_behavior(self, db_session, test_property_owner):
        """Test cascade delete behavior."""
        # Create property with related data
        property_obj = Property(
            title="Test Property",
            price=5000000.0,
            bhk=3,
            area=1200.0,
            property_type=PropertyType.APARTMENT,
            city="Mumbai",
            owner_id=test_property_owner.id
        )
        db_session.add(property_obj)
        db_session.commit()
        
        # Create related booking
        booking = PropertyBooking(
            booking_type=BookingType.VIEWING,
            property_id=property_obj.id,
            user_id=test_property_owner.id,
            preferred_date=datetime.utcnow() + timedelta(days=1),
            preferred_time="10:00"
        )
        db_session.add(booking)
        db_session.commit()
        
        # Verify relationships exist
        assert len(property_obj.property_bookings) == 1
        
        # Delete property
        db_session.delete(property_obj)
        db_session.commit()
        
        # Verify booking still exists (no cascade delete configured)
        remaining_booking = db_session.query(PropertyBooking).filter_by(id=booking.id).first()
        assert remaining_booking is not None
