"""
Unit tests for CRUD operations
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db import crud
from app.db.crud_bookings import (
    create_property_booking, get_property_booking, update_property_booking,
    delete_property_booking, get_user_bookings, get_property_bookings
)
from app.db.models import User, Property, Investment, PropertyBooking, BookingStatus


class TestUserCRUD:
    """Test User CRUD operations."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "+1234567890",
            "firebase_uid": "test_firebase_uid",
            "role": "tenant"
        }
        
        user = crud.create_user(db_session, user_data)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == "tenant"
        assert user.is_active is True
    
    def test_get_user_by_id(self, db_session, test_user):
        """Test getting user by ID."""
        retrieved_user = crud.get_user(db_session, user_id=test_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email
    
    def test_get_user_by_email(self, db_session, test_user):
        """Test getting user by email."""
        retrieved_user = crud.get_user_by_email(db_session, email=test_user.email)
        
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email
    
    def test_get_user_by_firebase_uid(self, db_session, test_user):
        """Test getting user by Firebase UID."""
        retrieved_user = crud.get_user_by_firebase_uid(db_session, firebase_uid=test_user.firebase_uid)
        
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.firebase_uid == test_user.firebase_uid
    
    def test_update_user(self, db_session, test_user):
        """Test updating user."""
        update_data = {
            "name": "Updated Name",
            "phone": "+9876543210",
            "kyc_verified": True
        }
        
        updated_user = crud.update_user(db_session, user_id=test_user.id, user_data=update_data)
        
        assert updated_user.name == "Updated Name"
        assert updated_user.phone == "+9876543210"
        assert updated_user.kyc_verified is True
        assert updated_user.email == test_user.email  # Unchanged
    
    def test_get_users_list(self, db_session):
        """Test getting list of users."""
        # Create multiple users
        for i in range(5):
            user_data = {
                "email": f"user{i}@example.com",
                "name": f"User {i}",
                "firebase_uid": f"uid_{i}",
                "role": "tenant"
            }
            crud.create_user(db_session, user_data)
        
        users = crud.get_users(db_session, skip=0, limit=10)
        
        assert len(users) == 5
        assert all(user.email.startswith("user") for user in users)
    
    def test_delete_user(self, db_session, test_user):
        """Test deleting user."""
        user_id = test_user.id
        
        deleted_user = crud.delete_user(db_session, user_id=user_id)
        
        assert deleted_user.id == user_id
        
        # Verify user is deleted
        retrieved_user = crud.get_user(db_session, user_id=user_id)
        assert retrieved_user is None


class TestPropertyCRUD:
    """Test Property CRUD operations."""
    
    def test_create_property(self, db_session, test_property_owner):
        """Test creating a property."""
        property_data = {
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
            "owner_id": test_property_owner.id
        }
        
        property_obj = crud.create_property(db_session, property_data)
        
        assert property_obj.id is not None
        assert property_obj.title == "Test Property"
        assert property_obj.price == 5000000.0
        assert property_obj.owner_id == test_property_owner.id
    
    def test_get_property_by_id(self, db_session, test_property):
        """Test getting property by ID."""
        retrieved_property = crud.get_property(db_session, property_id=test_property.id)
        
        assert retrieved_property is not None
        assert retrieved_property.id == test_property.id
        assert retrieved_property.title == test_property.title
    
    def test_update_property(self, db_session, test_property):
        """Test updating property."""
        update_data = {
            "title": "Updated Property Title",
            "price": 5500000.0,
            "is_verified": True
        }
        
        updated_property = crud.update_property(
            db_session, 
            property_id=test_property.id, 
            property_data=update_data
        )
        
        assert updated_property.title == "Updated Property Title"
        assert updated_property.price == 5500000.0
        assert updated_property.is_verified is True
        assert updated_property.bhk == test_property.bhk  # Unchanged
    
    def test_get_properties_list(self, db_session, test_property_owner):
        """Test getting list of properties."""
        # Create multiple properties
        for i in range(5):
            property_data = {
                "title": f"Property {i}",
                "price": 1000000.0 + i * 500000,
                "bhk": 2 + i,
                "area": 800.0 + i * 200,
                "property_type": "apartment",
                "city": "Mumbai",
                "owner_id": test_property_owner.id
            }
            crud.create_property(db_session, property_data)
        
        properties = crud.get_properties(db_session, skip=0, limit=10)
        
        assert len(properties) == 5
        assert all(prop.title.startswith("Property") for prop in properties)
    
    def test_get_properties_by_owner(self, db_session, test_property_owner):
        """Test getting properties by owner."""
        # Create properties for the owner
        for i in range(3):
            property_data = {
                "title": f"Owner Property {i}",
                "price": 2000000.0,
                "bhk": 2,
                "area": 1000.0,
                "property_type": "apartment",
                "city": "Mumbai",
                "owner_id": test_property_owner.id
            }
            crud.create_property(db_session, property_data)
        
        properties = crud.get_properties_by_owner(db_session, owner_id=test_property_owner.id)
        
        assert len(properties) == 3
        assert all(prop.owner_id == test_property_owner.id for prop in properties)
    
    def test_search_properties(self, db_session, test_property_owner):
        """Test searching properties."""
        # Create properties with different attributes
        properties_data = [
            {"title": "Mumbai Apartment", "city": "Mumbai", "bhk": 2, "price": 3000000.0},
            {"title": "Delhi House", "city": "Delhi", "bhk": 3, "price": 4000000.0},
            {"title": "Mumbai Villa", "city": "Mumbai", "bhk": 4, "price": 8000000.0},
        ]
        
        for prop_data in properties_data:
            prop_data.update({
                "area": 1000.0,
                "property_type": "apartment",
                "owner_id": test_property_owner.id
            })
            crud.create_property(db_session, prop_data)
        
        # Search by city
        mumbai_properties = crud.search_properties(db_session, city="Mumbai")
        assert len(mumbai_properties) == 2
        assert all(prop.city == "Mumbai" for prop in mumbai_properties)
        
        # Search by BHK
        three_bhk_properties = crud.search_properties(db_session, bhk=3)
        assert len(three_bhk_properties) == 1
        assert three_bhk_properties[0].bhk == 3
        
        # Search by price range
        affordable_properties = crud.search_properties(
            db_session, 
            min_price=2000000.0, 
            max_price=5000000.0
        )
        assert len(affordable_properties) == 2
    
    def test_delete_property(self, db_session, test_property):
        """Test deleting property."""
        property_id = test_property.id
        
        deleted_property = crud.delete_property(db_session, property_id=property_id)
        
        assert deleted_property.id == property_id
        
        # Verify property is deleted
        retrieved_property = crud.get_property(db_session, property_id=property_id)
        assert retrieved_property is None


class TestInvestmentCRUD:
    """Test Investment CRUD operations."""
    
    def test_create_investment(self, db_session, test_user, test_property):
        """Test creating an investment."""
        investment_data = {
            "title": "Test Investment",
            "amount": 1000000.0,
            "expected_roi": 12.5,
            "risk_level": "medium",
            "investment_type": "property",
            "duration_months": 24,
            "description": "A test investment opportunity",
            "location": "Mumbai",
            "investor_id": test_user.id,
            "property_id": test_property.id
        }
        
        investment = crud.create_investment(db_session, investment_data)
        
        assert investment.id is not None
        assert investment.title == "Test Investment"
        assert investment.amount == 1000000.0
        assert investment.investor_id == test_user.id
        assert investment.property_id == test_property.id
    
    def test_get_investment_by_id(self, db_session, test_investment):
        """Test getting investment by ID."""
        retrieved_investment = crud.get_investment(db_session, investment_id=test_investment.id)
        
        assert retrieved_investment is not None
        assert retrieved_investment.id == test_investment.id
        assert retrieved_investment.title == test_investment.title
    
    def test_get_investments_by_investor(self, db_session, test_user, test_property):
        """Test getting investments by investor."""
        # Create multiple investments for the user
        for i in range(3):
            investment_data = {
                "title": f"Investment {i}",
                "amount": 500000.0 + i * 100000,
                "expected_roi": 10.0 + i,
                "risk_level": "low",
                "investment_type": "property",
                "duration_months": 12,
                "investor_id": test_user.id,
                "property_id": test_property.id
            }
            crud.create_investment(db_session, investment_data)
        
        investments = crud.get_investments_by_investor(db_session, investor_id=test_user.id)
        
        assert len(investments) == 3
        assert all(inv.investor_id == test_user.id for inv in investments)
    
    def test_update_investment(self, db_session, test_investment):
        """Test updating investment."""
        update_data = {
            "status": "completed",
            "actual_roi": 13.2,
            "notes": "Investment completed successfully"
        }
        
        updated_investment = crud.update_investment(
            db_session,
            investment_id=test_investment.id,
            investment_data=update_data
        )
        
        assert updated_investment.status == "completed"
        assert updated_investment.actual_roi == 13.2
        assert updated_investment.notes == "Investment completed successfully"


class TestBookingCRUD:
    """Test Booking CRUD operations."""
    
    def test_create_property_booking(self, db_session, test_user, test_property):
        """Test creating a property booking."""
        booking_data = {
            "booking_type": "viewing",
            "property_id": test_property.id,
            "user_id": test_user.id,
            "preferred_date": datetime.utcnow() + timedelta(days=1),
            "preferred_time": "10:00",
            "duration_minutes": 60,
            "contact_name": "Test User",
            "contact_phone": "+1234567890",
            "contact_email": "test@example.com"
        }
        
        booking = create_property_booking(db_session, booking_data)
        
        assert booking.id is not None
        assert booking.booking_type == "viewing"
        assert booking.property_id == test_property.id
        assert booking.user_id == test_user.id
        assert booking.status == BookingStatus.PENDING
    
    def test_get_property_booking(self, db_session, test_booking):
        """Test getting property booking by ID."""
        retrieved_booking = get_property_booking(db_session, booking_id=test_booking.id)
        
        assert retrieved_booking is not None
        assert retrieved_booking.id == test_booking.id
        assert retrieved_booking.booking_type == test_booking.booking_type
    
    def test_update_property_booking(self, db_session, test_booking):
        """Test updating property booking."""
        update_data = {
            "status": BookingStatus.CONFIRMED,
            "confirmed_date": datetime.utcnow() + timedelta(days=1),
            "confirmed_time": "11:00",
            "notes": "Booking confirmed"
        }
        
        updated_booking = update_property_booking(
            db_session,
            booking_id=test_booking.id,
            booking_data=update_data
        )
        
        assert updated_booking.status == BookingStatus.CONFIRMED
        assert updated_booking.notes == "Booking confirmed"
    
    def test_get_user_bookings(self, db_session, test_user, test_property):
        """Test getting bookings by user."""
        # Create multiple bookings for the user
        for i in range(3):
            booking_data = {
                "booking_type": "viewing",
                "property_id": test_property.id,
                "user_id": test_user.id,
                "preferred_date": datetime.utcnow() + timedelta(days=i+1),
                "preferred_time": f"{10+i}:00",
                "duration_minutes": 60
            }
            create_property_booking(db_session, booking_data)
        
        bookings = get_user_bookings(db_session, user_id=test_user.id)
        
        assert len(bookings) == 3
        assert all(booking.user_id == test_user.id for booking in bookings)
    
    def test_get_property_bookings(self, db_session, test_user, test_property):
        """Test getting bookings by property."""
        # Create multiple bookings for the property
        for i in range(2):
            booking_data = {
                "booking_type": "viewing",
                "property_id": test_property.id,
                "user_id": test_user.id,
                "preferred_date": datetime.utcnow() + timedelta(days=i+1),
                "preferred_time": f"{10+i}:00",
                "duration_minutes": 60
            }
            create_property_booking(db_session, booking_data)
        
        bookings = get_property_bookings(db_session, property_id=test_property.id)
        
        assert len(bookings) == 2
        assert all(booking.property_id == test_property.id for booking in bookings)
    
    def test_delete_property_booking(self, db_session, test_booking):
        """Test deleting property booking."""
        booking_id = test_booking.id
        
        deleted_booking = delete_property_booking(db_session, booking_id=booking_id)
        
        assert deleted_booking.id == booking_id
        
        # Verify booking is deleted
        retrieved_booking = get_property_booking(db_session, booking_id=booking_id)
        assert retrieved_booking is None


class TestCRUDErrorHandling:
    """Test CRUD error handling."""
    
    def test_get_nonexistent_user(self, db_session):
        """Test getting non-existent user."""
        user = crud.get_user(db_session, user_id=99999)
        assert user is None
    
    def test_get_nonexistent_property(self, db_session):
        """Test getting non-existent property."""
        property_obj = crud.get_property(db_session, property_id=99999)
        assert property_obj is None
    
    def test_update_nonexistent_user(self, db_session):
        """Test updating non-existent user."""
        update_data = {"name": "Updated Name"}
        updated_user = crud.update_user(db_session, user_id=99999, user_data=update_data)
        assert updated_user is None
    
    def test_delete_nonexistent_property(self, db_session):
        """Test deleting non-existent property."""
        deleted_property = crud.delete_property(db_session, property_id=99999)
        assert deleted_property is None
