"""
Business logic validation for booking system
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db import models
from app.schemas.bookings import (
    PropertyBookingCreate, RentalApplicationCreate, PurchaseOfferCreate
)
import logging

logger = logging.getLogger(__name__)

class BookingValidationError(Exception):
    """Custom exception for booking validation errors"""
    pass

class BookingValidator:
    """Business logic validator for booking system"""

    @staticmethod
    def validate_property_booking(
        db: Session,
        booking_data: PropertyBookingCreate,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate property booking request"""
        try:
            # Check if property exists and is available
            property_obj = db.query(models.Property).filter(
                models.Property.id == booking_data.property_id
            ).first()
            
            if not property_obj:
                return False, "Property not found"
            
            if property_obj.status != models.PropertyStatus.AVAILABLE:
                return False, "Property is not available for booking"
            
            # Check if user is not the property owner
            if property_obj.owner_id == user_id:
                return False, "Property owners cannot book their own properties"
            
            # Validate booking date and time
            booking_datetime = booking_data.preferred_date
            current_time = datetime.utcnow()
            
            # Must be at least 1 hour in the future
            if booking_datetime <= current_time + timedelta(hours=1):
                return False, "Booking must be at least 1 hour in the future"
            
            # Cannot be more than 90 days in the future
            if booking_datetime > current_time + timedelta(days=90):
                return False, "Booking cannot be more than 90 days in the future"
            
            # Check business hours (9 AM to 6 PM)
            booking_hour = int(booking_data.preferred_time.split(':')[0])
            if booking_hour < 9 or booking_hour >= 18:
                return False, "Bookings are only available between 9 AM and 6 PM"
            
            # Check for conflicting bookings
            booking_start = booking_datetime
            booking_end = booking_start + timedelta(minutes=booking_data.duration_minutes)
            
            existing_bookings = db.query(models.PropertyBooking).filter(
                models.PropertyBooking.property_id == booking_data.property_id,
                models.PropertyBooking.status == models.BookingStatus.CONFIRMED
            ).all()
            
            for existing in existing_bookings:
                if existing.preferred_date and existing.duration_minutes:
                    existing_start = existing.preferred_date
                    existing_end = existing_start + timedelta(minutes=existing.duration_minutes)
                    
                    # Check for overlap
                    if (booking_start < existing_end and booking_end > existing_start):
                        return False, f"Time slot conflicts with existing booking at {existing_start.strftime('%Y-%m-%d %H:%M')}"
            
            # Validate duration
            if booking_data.duration_minutes < 15:
                return False, "Minimum booking duration is 15 minutes"
            
            if booking_data.duration_minutes > 480:  # 8 hours
                return False, "Maximum booking duration is 8 hours"
            
            # Check daily booking limit per user (max 3 bookings per day)
            booking_date = booking_datetime.date()
            daily_bookings = db.query(models.PropertyBooking).filter(
                models.PropertyBooking.user_id == user_id,
                models.PropertyBooking.preferred_date >= datetime.combine(booking_date, datetime.min.time()),
                models.PropertyBooking.preferred_date < datetime.combine(booking_date + timedelta(days=1), datetime.min.time()),
                models.PropertyBooking.status.in_([models.BookingStatus.PENDING, models.BookingStatus.CONFIRMED])
            ).count()
            
            if daily_bookings >= 3:
                return False, "Maximum 3 bookings allowed per day"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating property booking: {str(e)}")
            return False, "Validation error occurred"

    @staticmethod
    def validate_rental_application(
        db: Session,
        application_data: RentalApplicationCreate,
        applicant_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate rental application"""
        try:
            # Check if property exists and is available for rent
            property_obj = db.query(models.Property).filter(
                models.Property.id == application_data.property_id
            ).first()
            
            if not property_obj:
                return False, "Property not found"
            
            if property_obj.status != models.PropertyStatus.AVAILABLE:
                return False, "Property is not available for rental"
            
            if property_obj.property_type not in [models.PropertyType.APARTMENT, models.PropertyType.HOUSE, models.PropertyType.VILLA]:
                return False, "Property type is not suitable for rental"
            
            # Check if user is not the property owner
            if property_obj.owner_id == applicant_id:
                return False, "Property owners cannot apply for their own properties"
            
            # Check if user already has a pending application
            existing_application = db.query(models.RentalApplication).filter(
                models.RentalApplication.property_id == application_data.property_id,
                models.RentalApplication.applicant_id == applicant_id,
                models.RentalApplication.status.in_([
                    models.ApplicationStatus.SUBMITTED,
                    models.ApplicationStatus.UNDER_REVIEW
                ])
            ).first()
            
            if existing_application:
                return False, "You already have a pending application for this property"
            
            # Validate move-in date
            move_in_date = application_data.desired_move_in_date
            current_date = datetime.utcnow().date()
            
            if move_in_date.date() <= current_date:
                return False, "Move-in date must be in the future"
            
            if move_in_date.date() > current_date + timedelta(days=365):
                return False, "Move-in date cannot be more than 1 year in the future"
            
            # Validate lease duration
            if application_data.lease_duration_months < 1:
                return False, "Minimum lease duration is 1 month"
            
            if application_data.lease_duration_months > 60:
                return False, "Maximum lease duration is 60 months"
            
            # Validate offered rent (should be reasonable compared to property price)
            if property_obj.price:
                monthly_rent_estimate = property_obj.price * 0.001  # 0.1% of property value per month
                if application_data.offered_rent < monthly_rent_estimate * 0.5:
                    return False, "Offered rent is too low compared to property value"
                
                if application_data.offered_rent > monthly_rent_estimate * 2:
                    return False, "Offered rent is unusually high"
            
            # Validate income (should be at least 3x the rent)
            if application_data.monthly_income < application_data.offered_rent * 3:
                return False, "Monthly income should be at least 3 times the offered rent"
            
            # Validate security deposit
            if application_data.security_deposit < application_data.offered_rent:
                return False, "Security deposit should be at least one month's rent"
            
            if application_data.security_deposit > application_data.offered_rent * 6:
                return False, "Security deposit cannot exceed 6 months' rent"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating rental application: {str(e)}")
            return False, "Validation error occurred"

    @staticmethod
    def validate_purchase_offer(
        db: Session,
        offer_data: PurchaseOfferCreate,
        buyer_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate purchase offer"""
        try:
            # Check if property exists and is available for sale
            property_obj = db.query(models.Property).filter(
                models.Property.id == offer_data.property_id
            ).first()
            
            if not property_obj:
                return False, "Property not found"
            
            if property_obj.status != models.PropertyStatus.AVAILABLE:
                return False, "Property is not available for purchase"
            
            # Check if user is not the property owner
            if property_obj.owner_id == buyer_id:
                return False, "Property owners cannot make offers on their own properties"
            
            # Validate offer price
            if offer_data.offered_price <= 0:
                return False, "Offer price must be greater than 0"
            
            if property_obj.price:
                # Offer should be reasonable (between 50% and 150% of listed price)
                min_offer = property_obj.price * 0.5
                max_offer = property_obj.price * 1.5
                
                if offer_data.offered_price < min_offer:
                    return False, f"Offer price is too low (minimum: ₹{min_offer:,.2f})"
                
                if offer_data.offered_price > max_offer:
                    return False, f"Offer price is too high (maximum: ₹{max_offer:,.2f})"
            
            # Validate financing
            if offer_data.financing_type not in ["cash", "mortgage", "mixed"]:
                return False, "Invalid financing type"
            
            if offer_data.financing_type == "cash":
                if offer_data.loan_amount > 0:
                    return False, "Cash offers cannot have loan amount"
                if offer_data.down_payment != offer_data.offered_price:
                    return False, "Cash offers require full down payment"
            
            if offer_data.financing_type in ["mortgage", "mixed"]:
                if offer_data.down_payment < offer_data.offered_price * 0.1:
                    return False, "Minimum down payment is 10% of offer price"
                
                if offer_data.down_payment > offer_data.offered_price:
                    return False, "Down payment cannot exceed offer price"
                
                expected_loan = offer_data.offered_price - offer_data.down_payment
                if abs(offer_data.loan_amount - expected_loan) > 1000:
                    return False, "Loan amount should equal offer price minus down payment"
            
            # Validate dates
            current_date = datetime.utcnow()
            
            if offer_data.closing_date <= current_date + timedelta(days=30):
                return False, "Closing date must be at least 30 days from now"
            
            if offer_data.closing_date > current_date + timedelta(days=180):
                return False, "Closing date cannot be more than 180 days from now"
            
            if offer_data.expiration_date <= current_date + timedelta(hours=24):
                return False, "Offer expiration must be at least 24 hours from now"
            
            if offer_data.expiration_date > current_date + timedelta(days=30):
                return False, "Offer expiration cannot be more than 30 days from now"
            
            # Validate earnest money
            if offer_data.earnest_money < offer_data.offered_price * 0.01:
                return False, "Earnest money should be at least 1% of offer price"
            
            if offer_data.earnest_money > offer_data.offered_price * 0.1:
                return False, "Earnest money should not exceed 10% of offer price"
            
            # Validate contingency periods
            if offer_data.inspection_period_days < 0 or offer_data.inspection_period_days > 30:
                return False, "Inspection period must be between 0 and 30 days"
            
            if offer_data.financing_contingency_days < 0 or offer_data.financing_contingency_days > 60:
                return False, "Financing contingency must be between 0 and 60 days"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating purchase offer: {str(e)}")
            return False, "Validation error occurred"

    @staticmethod
    def get_booking_availability(
        db: Session,
        property_id: int,
        date: datetime,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a property on a specific date"""
        try:
            # Business hours: 9 AM to 6 PM
            start_hour = 9
            end_hour = 18
            slot_duration = duration_minutes
            
            # Get existing bookings for the date
            date_start = datetime.combine(date.date(), datetime.min.time())
            date_end = date_start + timedelta(days=1)
            
            existing_bookings = db.query(models.PropertyBooking).filter(
                models.PropertyBooking.property_id == property_id,
                models.PropertyBooking.preferred_date >= date_start,
                models.PropertyBooking.preferred_date < date_end,
                models.PropertyBooking.status == models.BookingStatus.CONFIRMED
            ).all()
            
            # Generate all possible time slots
            available_slots = []
            current_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=start_hour)
            end_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=end_hour)
            
            while current_time + timedelta(minutes=slot_duration) <= end_time:
                slot_end = current_time + timedelta(minutes=slot_duration)
                
                # Check if slot conflicts with existing bookings
                is_available = True
                for booking in existing_bookings:
                    booking_start = booking.preferred_date
                    booking_end = booking_start + timedelta(minutes=booking.duration_minutes)
                    
                    if (current_time < booking_end and slot_end > booking_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        "start_time": current_time.strftime("%H:%M"),
                        "end_time": slot_end.strftime("%H:%M"),
                        "datetime": current_time,
                        "available": True
                    })
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting booking availability: {str(e)}")
            return []
