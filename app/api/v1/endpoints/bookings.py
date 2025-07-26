from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db import crud_bookings, models
from app.core.security import get_current_active_user
from app.schemas.bookings import (
    PropertyBookingCreate, PropertyBookingUpdate, PropertyBookingStatusUpdate, PropertyBookingOut,
    RentalApplicationCreate, RentalApplicationUpdate, RentalApplicationReview, RentalApplicationOut,
    PurchaseOfferCreate, PurchaseOfferUpdate, PurchaseOfferReview, PurchaseOfferOut,
    BookingSummary, ApplicationSummary, OfferSummary, BookingAnalytics
)
from app.utils.notifications import create_notification
from app.utils.email import send_booking_confirmation_email, send_application_notification_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Property Booking Endpoints

@router.post("/property-bookings", response_model=PropertyBookingOut)
async def create_property_booking(
    booking_data: PropertyBookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new property booking"""
    try:
        # Verify property exists
        property_obj = db.query(models.Property).filter(models.Property.id == booking_data.property_id).first()
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check if property is available
        if property_obj.status not in [models.PropertyStatus.AVAILABLE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property is not available for booking"
            )
        
        # Check for conflicting bookings
        existing_bookings = crud_bookings.get_property_bookings(
            db=db,
            property_id=booking_data.property_id,
            status=models.BookingStatus.CONFIRMED.value
        )
        
        booking_start = booking_data.preferred_date
        booking_end = booking_start + timedelta(minutes=booking_data.duration_minutes)
        
        for existing in existing_bookings:
            if existing.preferred_date and existing.duration_minutes:
                existing_start = existing.preferred_date
                existing_end = existing_start + timedelta(minutes=existing.duration_minutes)
                
                if (booking_start < existing_end and booking_end > existing_start):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Time slot is already booked"
                    )
        
        # Create booking
        booking = crud_bookings.create_property_booking(
            db=db,
            booking_data=booking_data,
            user_id=getattr(current_user, 'id')
        )
        
        # Send notifications
        background_tasks.add_task(
            create_notification,
            db=db,
            user_id=property_obj.owner_id,
            title="New Property Booking",
            message=f"New {booking_data.booking_type} booking for {property_obj.title}",
            notification_type="booking_created"
        )
        
        background_tasks.add_task(
            send_booking_confirmation_email,
            booking_id=booking.id,
            user_email=getattr(current_user, 'email')
        )
        
        return booking
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating property booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking"
        )

@router.get("/property-bookings", response_model=List[PropertyBookingOut])
async def get_property_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    property_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    booking_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get property bookings for current user"""
    return crud_bookings.get_property_bookings(
        db=db,
        skip=skip,
        limit=limit,
        user_id=getattr(current_user, 'id'),
        property_id=property_id,
        status=status,
        booking_type=booking_type
    )

@router.get("/property-bookings/{booking_id}", response_model=PropertyBookingOut)
async def get_property_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get a specific property booking"""
    booking = crud_bookings.get_property_booking(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user owns the booking or the property
    if (booking.user_id != getattr(current_user, 'id') and 
        booking.property.owner_id != getattr(current_user, 'id')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )
    
    return booking

@router.put("/property-bookings/{booking_id}", response_model=PropertyBookingOut)
async def update_property_booking(
    booking_id: int,
    booking_update: PropertyBookingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update a property booking"""
    booking = crud_bookings.get_property_booking(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Only booking owner can update
    if booking.user_id != getattr(current_user, 'id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this booking"
        )
    
    # Can only update pending bookings
    if booking.status != models.BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update pending bookings"
        )
    
    updated_booking = crud_bookings.update_property_booking(
        db=db,
        booking_id=booking_id,
        booking_update=booking_update
    )
    
    return updated_booking

@router.put("/property-bookings/{booking_id}/status", response_model=PropertyBookingOut)
async def update_booking_status(
    booking_id: int,
    status_update: PropertyBookingStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update booking status (for property owners)"""
    booking = crud_bookings.get_property_booking(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Only property owner can update status
    if booking.property.owner_id != getattr(current_user, 'id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owner can update booking status"
        )
    
    updated_booking = crud_bookings.update_booking_status(
        db=db,
        booking_id=booking_id,
        status_update=status_update
    )
    
    # Send notification to booking user
    background_tasks.add_task(
        create_notification,
        db=db,
        user_id=booking.user_id,
        title="Booking Status Updated",
        message=f"Your booking status has been updated to {status_update.status}",
        notification_type="booking_status_updated"
    )
    
    return updated_booking

@router.get("/property-bookings/upcoming", response_model=List[PropertyBookingOut])
async def get_upcoming_bookings(
    days_ahead: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get upcoming bookings for current user"""
    return crud_bookings.get_upcoming_bookings(
        db=db,
        user_id=getattr(current_user, 'id'),
        days_ahead=days_ahead
    )

# Rental Application Endpoints

@router.post("/rental-applications", response_model=RentalApplicationOut)
async def create_rental_application(
    application_data: RentalApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new rental application"""
    try:
        # Verify property exists and is available for rent
        property_obj = db.query(models.Property).filter(models.Property.id == application_data.property_id).first()
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        if property_obj.status != models.PropertyStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property is not available for rental"
            )
        
        # Check if user already has a pending application for this property
        existing_application = db.query(models.RentalApplication).filter(
            models.RentalApplication.property_id == application_data.property_id,
            models.RentalApplication.applicant_id == getattr(current_user, 'id'),
            models.RentalApplication.status.in_([
                models.ApplicationStatus.SUBMITTED,
                models.ApplicationStatus.UNDER_REVIEW
            ])
        ).first()
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a pending application for this property"
            )
        
        # Create application
        application = crud_bookings.create_rental_application(
            db=db,
            application_data=application_data,
            applicant_id=getattr(current_user, 'id')
        )
        
        # Send notifications
        background_tasks.add_task(
            create_notification,
            db=db,
            user_id=property_obj.owner_id,
            title="New Rental Application",
            message=f"New rental application for {property_obj.title}",
            notification_type="application_submitted"
        )
        
        background_tasks.add_task(
            send_application_notification_email,
            application_id=application.id,
            property_owner_email=property_obj.owner.email
        )
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rental application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rental application"
        )

@router.get("/rental-applications", response_model=List[RentalApplicationOut])
async def get_rental_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    property_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get rental applications for current user"""
    return crud_bookings.get_rental_applications(
        db=db,
        skip=skip,
        limit=limit,
        applicant_id=getattr(current_user, 'id'),
        property_id=property_id,
        status=status
    )

@router.put("/rental-applications/{application_id}/review", response_model=RentalApplicationOut)
async def review_rental_application(
    application_id: int,
    review_data: RentalApplicationReview,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Review a rental application (for property owners)"""
    application = crud_bookings.get_rental_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Only property owner can review
    if application.property.owner_id != getattr(current_user, 'id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owner can review applications"
        )

    updated_application = crud_bookings.review_rental_application(
        db=db,
        application_id=application_id,
        review_data=review_data,
        reviewer_id=getattr(current_user, 'id')
    )

    # Send notification to applicant
    background_tasks.add_task(
        create_notification,
        db=db,
        user_id=application.applicant_id,
        title="Application Reviewed",
        message=f"Your rental application has been {review_data.status}",
        notification_type="application_reviewed"
    )

    return updated_application

# Purchase Offer Endpoints

@router.post("/purchase-offers", response_model=PurchaseOfferOut)
async def create_purchase_offer(
    offer_data: PurchaseOfferCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new purchase offer"""
    try:
        # Verify property exists and is available for sale
        property_obj = db.query(models.Property).filter(models.Property.id == offer_data.property_id).first()
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        if property_obj.status != models.PropertyStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property is not available for purchase"
            )

        # Validate offer amount
        if offer_data.offered_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offer price must be greater than 0"
            )

        # Create offer
        offer = crud_bookings.create_purchase_offer(
            db=db,
            offer_data=offer_data,
            buyer_id=getattr(current_user, 'id')
        )

        # Send notifications
        background_tasks.add_task(
            create_notification,
            db=db,
            user_id=property_obj.owner_id,
            title="New Purchase Offer",
            message=f"New purchase offer for {property_obj.title} - ₹{offer_data.offered_price:,.2f}",
            notification_type="offer_submitted"
        )

        return offer

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating purchase offer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase offer"
        )

@router.get("/purchase-offers", response_model=List[PurchaseOfferOut])
async def get_purchase_offers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    property_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get purchase offers for current user"""
    return crud_bookings.get_purchase_offers(
        db=db,
        skip=skip,
        limit=limit,
        buyer_id=getattr(current_user, 'id'),
        property_id=property_id,
        status=status
    )

@router.put("/purchase-offers/{offer_id}/review", response_model=PurchaseOfferOut)
async def review_purchase_offer(
    offer_id: int,
    review_data: PurchaseOfferReview,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Review a purchase offer (for property owners)"""
    offer = crud_bookings.get_purchase_offer(db=db, offer_id=offer_id)
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )

    # Only property owner can review
    if offer.property.owner_id != getattr(current_user, 'id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only property owner can review offers"
        )

    updated_offer = crud_bookings.review_purchase_offer(
        db=db,
        offer_id=offer_id,
        review_data=review_data,
        reviewer_id=getattr(current_user, 'id')
    )

    # Send notification to buyer
    notification_message = f"Your purchase offer has been {review_data.status}"
    if review_data.counter_offer_price:
        notification_message += f" with counter offer of ₹{review_data.counter_offer_price:,.2f}"

    background_tasks.add_task(
        create_notification,
        db=db,
        user_id=offer.buyer_id,
        title="Offer Reviewed",
        message=notification_message,
        notification_type="offer_reviewed"
    )

    return updated_offer

# Analytics Endpoints

@router.get("/analytics/bookings", response_model=dict)
async def get_booking_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get booking analytics for current user"""
    return crud_bookings.get_booking_summary(db=db, user_id=getattr(current_user, 'id'))

@router.get("/analytics/property/{property_id}/bookings", response_model=dict)
async def get_property_booking_analytics(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get booking analytics for a specific property"""
    # Verify property ownership
    property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    if property_obj.owner_id != getattr(current_user, 'id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view analytics for this property"
        )

    return crud_bookings.get_property_booking_analytics(db=db, property_id=property_id)
