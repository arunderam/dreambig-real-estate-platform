from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.db import models
from app.schemas.bookings import (
    PropertyBookingCreate, PropertyBookingUpdate, PropertyBookingStatusUpdate,
    RentalApplicationCreate, RentalApplicationUpdate, RentalApplicationReview,
    PurchaseOfferCreate, PurchaseOfferUpdate, PurchaseOfferReview
)

# Property Booking CRUD Operations

def create_property_booking(db: Session, booking_data: PropertyBookingCreate, user_id: int) -> models.PropertyBooking:
    """Create a new property booking"""
    db_booking = models.PropertyBooking(
        **booking_data.dict(),
        user_id=user_id
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_property_booking(db: Session, booking_id: int) -> Optional[models.PropertyBooking]:
    """Get a property booking by ID"""
    return db.query(models.PropertyBooking).filter(models.PropertyBooking.id == booking_id).first()

def get_property_bookings(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    user_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    booking_type: Optional[str] = None
) -> List[models.PropertyBooking]:
    """Get property bookings with filters"""
    query = db.query(models.PropertyBooking)
    
    if user_id:
        query = query.filter(models.PropertyBooking.user_id == user_id)
    if property_id:
        query = query.filter(models.PropertyBooking.property_id == property_id)
    if status:
        query = query.filter(models.PropertyBooking.status == status)
    if booking_type:
        query = query.filter(models.PropertyBooking.booking_type == booking_type)
    
    return query.order_by(desc(models.PropertyBooking.created_at)).offset(skip).limit(limit).all()

def update_property_booking(
    db: Session, 
    booking_id: int, 
    booking_update: PropertyBookingUpdate
) -> Optional[models.PropertyBooking]:
    """Update a property booking"""
    db_booking = get_property_booking(db, booking_id)
    if not db_booking:
        return None
    
    update_data = booking_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_booking, field, value)
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

def update_booking_status(
    db: Session, 
    booking_id: int, 
    status_update: PropertyBookingStatusUpdate
) -> Optional[models.PropertyBooking]:
    """Update booking status"""
    db_booking = get_property_booking(db, booking_id)
    if not db_booking:
        return None
    
    db_booking.status = status_update.status
    if status_update.confirmed_date:
        db_booking.confirmed_date = status_update.confirmed_date
    if status_update.cancellation_reason:
        db_booking.cancellation_reason = status_update.cancellation_reason
    
    if status_update.status == models.BookingStatus.COMPLETED:
        db_booking.completed_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_upcoming_bookings(db: Session, user_id: int, days_ahead: int = 7) -> List[models.PropertyBooking]:
    """Get upcoming bookings for a user"""
    end_date = datetime.utcnow() + timedelta(days=days_ahead)
    return db.query(models.PropertyBooking).filter(
        and_(
            models.PropertyBooking.user_id == user_id,
            models.PropertyBooking.status == models.BookingStatus.CONFIRMED,
            models.PropertyBooking.preferred_date >= datetime.utcnow(),
            models.PropertyBooking.preferred_date <= end_date
        )
    ).order_by(models.PropertyBooking.preferred_date).all()

# Rental Application CRUD Operations

def create_rental_application(
    db: Session, 
    application_data: RentalApplicationCreate, 
    applicant_id: int
) -> models.RentalApplication:
    """Create a new rental application"""
    db_application = models.RentalApplication(
        **application_data.dict(),
        applicant_id=applicant_id
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def get_rental_application(db: Session, application_id: int) -> Optional[models.RentalApplication]:
    """Get a rental application by ID"""
    return db.query(models.RentalApplication).filter(models.RentalApplication.id == application_id).first()

def get_rental_applications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    applicant_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[models.RentalApplication]:
    """Get rental applications with filters"""
    query = db.query(models.RentalApplication)
    
    if applicant_id:
        query = query.filter(models.RentalApplication.applicant_id == applicant_id)
    if property_id:
        query = query.filter(models.RentalApplication.property_id == property_id)
    if status:
        query = query.filter(models.RentalApplication.status == status)
    
    return query.order_by(desc(models.RentalApplication.created_at)).offset(skip).limit(limit).all()

def update_rental_application(
    db: Session,
    application_id: int,
    application_update: RentalApplicationUpdate
) -> Optional[models.RentalApplication]:
    """Update a rental application"""
    db_application = get_rental_application(db, application_id)
    if not db_application:
        return None
    
    update_data = application_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_application, field, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application

def review_rental_application(
    db: Session,
    application_id: int,
    review_data: RentalApplicationReview,
    reviewer_id: int
) -> Optional[models.RentalApplication]:
    """Review a rental application"""
    db_application = get_rental_application(db, application_id)
    if not db_application:
        return None
    
    db_application.status = review_data.status
    db_application.review_notes = review_data.review_notes
    db_application.reviewed_by = reviewer_id
    db_application.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_application)
    return db_application

# Purchase Offer CRUD Operations

def create_purchase_offer(
    db: Session,
    offer_data: PurchaseOfferCreate,
    buyer_id: int
) -> models.PurchaseOffer:
    """Create a new purchase offer"""
    db_offer = models.PurchaseOffer(
        **offer_data.dict(),
        buyer_id=buyer_id
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    return db_offer

def get_purchase_offer(db: Session, offer_id: int) -> Optional[models.PurchaseOffer]:
    """Get a purchase offer by ID"""
    return db.query(models.PurchaseOffer).filter(models.PurchaseOffer.id == offer_id).first()

def get_purchase_offers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    buyer_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[models.PurchaseOffer]:
    """Get purchase offers with filters"""
    query = db.query(models.PurchaseOffer)
    
    if buyer_id:
        query = query.filter(models.PurchaseOffer.buyer_id == buyer_id)
    if property_id:
        query = query.filter(models.PurchaseOffer.property_id == property_id)
    if status:
        query = query.filter(models.PurchaseOffer.status == status)
    
    return query.order_by(desc(models.PurchaseOffer.created_at)).offset(skip).limit(limit).all()

def update_purchase_offer(
    db: Session,
    offer_id: int,
    offer_update: PurchaseOfferUpdate
) -> Optional[models.PurchaseOffer]:
    """Update a purchase offer"""
    db_offer = get_purchase_offer(db, offer_id)
    if not db_offer:
        return None
    
    update_data = offer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_offer, field, value)
    
    db.commit()
    db.refresh(db_offer)
    return db_offer

def review_purchase_offer(
    db: Session,
    offer_id: int,
    review_data: PurchaseOfferReview,
    reviewer_id: int
) -> Optional[models.PurchaseOffer]:
    """Review a purchase offer"""
    db_offer = get_purchase_offer(db, offer_id)
    if not db_offer:
        return None
    
    db_offer.status = review_data.status
    db_offer.review_notes = review_data.review_notes
    db_offer.reviewed_by = reviewer_id
    db_offer.reviewed_at = datetime.utcnow()
    
    if review_data.counter_offer_price:
        db_offer.counter_offer_price = review_data.counter_offer_price
        db_offer.counter_offer_terms = review_data.counter_offer_terms
        db_offer.counter_offer_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_offer)
    return db_offer

# Analytics and Summary Functions

def get_booking_summary(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Get booking summary statistics"""
    query = db.query(models.PropertyBooking)
    if user_id:
        query = query.filter(models.PropertyBooking.user_id == user_id)
    
    total = query.count()
    pending = query.filter(models.PropertyBooking.status == models.BookingStatus.PENDING).count()
    confirmed = query.filter(models.PropertyBooking.status == models.BookingStatus.CONFIRMED).count()
    completed = query.filter(models.PropertyBooking.status == models.BookingStatus.COMPLETED).count()
    cancelled = query.filter(models.PropertyBooking.status == models.BookingStatus.CANCELLED).count()
    
    return {
        "total_bookings": total,
        "pending_bookings": pending,
        "confirmed_bookings": confirmed,
        "completed_bookings": completed,
        "cancelled_bookings": cancelled
    }

def get_property_booking_analytics(db: Session, property_id: int) -> Dict[str, Any]:
    """Get booking analytics for a specific property"""
    bookings = db.query(models.PropertyBooking).filter(
        models.PropertyBooking.property_id == property_id
    ).all()
    
    total_bookings = len(bookings)
    if total_bookings == 0:
        return {
            "property_id": property_id,
            "total_bookings": 0,
            "conversion_rate": 0,
            "average_duration": 0,
            "popular_times": []
        }
    
    # Calculate popular time slots
    time_slots = {}
    total_duration = 0
    
    for booking in bookings:
        if booking.preferred_time:
            hour = booking.preferred_time.split(':')[0]
            time_slots[hour] = time_slots.get(hour, 0) + 1
        
        if booking.duration_minutes:
            total_duration += booking.duration_minutes
    
    popular_times = sorted(time_slots.items(), key=lambda x: x[1], reverse=True)[:5]
    average_duration = total_duration / total_bookings if total_bookings > 0 else 0
    
    return {
        "property_id": property_id,
        "total_bookings": total_bookings,
        "average_duration": average_duration,
        "popular_times": [{"hour": hour, "count": count} for hour, count in popular_times]
    }
