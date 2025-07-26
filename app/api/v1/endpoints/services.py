from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import crud, models
from app.db.session import get_db
from app.schemas.services import (
    ServiceProviderCreate,
    ServiceProviderOut,
    ServiceBookingCreate,
    ServiceBookingOut
)
from app.core.security import get_current_active_user
from app.utils import send_email, send_sms

router = APIRouter()

@router.get("/", response_model=List[ServiceProviderOut])
async def get_services(
    category: Optional[str] = None,
    service_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get services with optional filtering by category or service type"""
    query = db.query(models.ServiceProvider)

    # Filter by category (map category to service_type)
    if category:
        query = query.filter(models.ServiceProvider.service_type == category)
    elif service_type:
        query = query.filter(models.ServiceProvider.service_type == service_type)

    # Only return verified providers
    query = query.filter(models.ServiceProvider.is_verified == True)

    return query.offset(skip).limit(limit).all()

@router.post("/providers", response_model=ServiceProviderOut)
async def create_service_provider(
    provider_data: ServiceProviderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Register a new service provider"""
    if current_user.role not in ["admin", "service_provider"]: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or service providers can register providers"
        )
    
    return crud.create_service_provider(db, provider_data.dict())

@router.get("/providers", response_model=List[ServiceProviderOut])
async def list_service_providers(
    service_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all service providers with optional filtering"""
    query = db.query(models.ServiceProvider)
    if service_type:
        query = query.filter(models.ServiceProvider.service_type == service_type)
    return query.offset(skip).limit(limit).all()

@router.post("/bookings", response_model=ServiceBookingOut)
async def create_service_booking(
    booking_data: ServiceBookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new service booking"""
    # Verify service provider exists
    provider = crud.get_service_provider(db, booking_data.service_provider_id) # type: ignore
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service provider not found"
        )
    
    # Verify property exists if provided
    if booking_data.property_id:
        property = crud.get_property(db, booking_data.property_id)
        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
    
    # Create booking
    booking = crud.create_service_booking(
        db,
        {
            **booking_data.dict(),
            "user_id": current_user.id, # type: ignore
            "status": "pending"
        }
    )
    
    # Send notifications
    background_tasks.add_task(
        send_email,
        email_to=provider.email,
        subject="New Service Booking",
        body=f"You have a new booking request from {current_user.name}" # type: ignore
    ) # type: ignore
    
    background_tasks.add_task(
        send_sms,
        phone_numbers=[provider.contact_number],
        message=f"New booking request from {current_user.name}" # type: ignore
    ) # type: ignore
    
    return booking

@router.get("/bookings", response_model=List[ServiceBookingOut])
async def get_my_bookings(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all bookings for current user"""
    query = db.query(models.ServiceBooking).filter(
        models.ServiceBooking.user_id == current_user.id # type: ignore
    )
    if status:
        query = query.filter(models.ServiceBooking.status == status)
    return query.order_by(models.ServiceBooking.created_at.desc()).all()

@router.put("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    new_status: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update booking status (for providers)"""
    booking = crud.get_service_booking(db, booking_id) # type: ignore
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Verify current user is the provider
    if booking.service_provider_id != current_user.id: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the service provider can update status"
        )
    
    # Update status
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    
    # Notify user
    user = crud.get_user(db, booking.user_id)
    if user and user.email: # pyright: ignore[reportGeneralTypeIssues]
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="Booking Status Update",
            body=f"Your booking #{booking_id} status changed to {new_status}"
        ) # type: ignore
    
    return {"message": "Booking status updated"}