from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models import BookingType, BookingStatus, ApplicationStatus, OfferStatus

# Property Booking Schemas
class PropertyBookingBase(BaseModel):
    booking_type: BookingType
    property_id: int = Field(..., gt=0)
    preferred_date: datetime
    preferred_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    duration_minutes: int = Field(default=60, ge=15, le=480)
    notes: Optional[str] = Field(None, max_length=1000)
    special_requirements: Optional[str] = Field(None, max_length=500)
    contact_name: str = Field(..., min_length=2, max_length=100)
    contact_phone: str = Field(..., min_length=10, max_length=15)
    contact_email: EmailStr

class PropertyBookingCreate(PropertyBookingBase):
    pass

class PropertyBookingUpdate(BaseModel):
    preferred_date: Optional[datetime] = None
    preferred_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    notes: Optional[str] = Field(None, max_length=1000)
    special_requirements: Optional[str] = Field(None, max_length=500)
    contact_name: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_phone: Optional[str] = Field(None, min_length=10, max_length=15)
    contact_email: Optional[EmailStr] = None

class PropertyBookingStatusUpdate(BaseModel):
    status: BookingStatus
    confirmed_date: Optional[datetime] = None
    cancellation_reason: Optional[str] = Field(None, max_length=500)

class PropertyBookingOut(PropertyBookingBase):
    id: int
    user_id: int
    status: BookingStatus
    confirmed_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Rental Application Schemas
class RentalApplicationBase(BaseModel):
    property_id: int = Field(..., gt=0)
    desired_move_in_date: datetime
    lease_duration_months: int = Field(..., ge=1, le=60)
    offered_rent: float = Field(..., gt=0)
    security_deposit: float = Field(..., ge=0)
    employment_status: str = Field(..., max_length=100)
    employer_name: Optional[str] = Field(None, max_length=200)
    monthly_income: float = Field(..., gt=0)
    previous_address: Optional[str] = Field(None, max_length=500)
    references: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    background_check_consent: bool = False

class RentalApplicationCreate(RentalApplicationBase):
    documents: Optional[List[str]] = Field(default_factory=list)

class RentalApplicationUpdate(BaseModel):
    desired_move_in_date: Optional[datetime] = None
    lease_duration_months: Optional[int] = Field(None, ge=1, le=60)
    offered_rent: Optional[float] = Field(None, gt=0)
    security_deposit: Optional[float] = Field(None, ge=0)
    employment_status: Optional[str] = Field(None, max_length=100)
    employer_name: Optional[str] = Field(None, max_length=200)
    monthly_income: Optional[float] = Field(None, gt=0)
    previous_address: Optional[str] = Field(None, max_length=500)
    references: Optional[List[Dict[str, Any]]] = None
    background_check_consent: Optional[bool] = None

class RentalApplicationReview(BaseModel):
    status: ApplicationStatus
    review_notes: Optional[str] = Field(None, max_length=1000)

class RentalApplicationOut(RentalApplicationBase):
    id: int
    applicant_id: int
    status: ApplicationStatus
    documents: Optional[List[str]] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Purchase Offer Schemas
class PurchaseOfferBase(BaseModel):
    property_id: int = Field(..., gt=0)
    offered_price: float = Field(..., gt=0)
    financing_type: str = Field(..., pattern=r"^(cash|mortgage|mixed)$")
    down_payment: float = Field(..., ge=0)
    loan_amount: float = Field(default=0, ge=0)
    contingencies: Optional[List[str]] = Field(default_factory=list)
    closing_date: datetime
    inspection_period_days: int = Field(default=7, ge=0, le=30)
    financing_contingency_days: int = Field(default=30, ge=0, le=60)
    earnest_money: float = Field(..., ge=0)
    additional_terms: Optional[str] = Field(None, max_length=2000)
    expiration_date: datetime

class PurchaseOfferCreate(PurchaseOfferBase):
    pass

class PurchaseOfferUpdate(BaseModel):
    offered_price: Optional[float] = Field(None, gt=0)
    financing_type: Optional[str] = Field(None, pattern=r"^(cash|mortgage|mixed)$")
    down_payment: Optional[float] = Field(None, ge=0)
    loan_amount: Optional[float] = Field(None, ge=0)
    contingencies: Optional[List[str]] = None
    closing_date: Optional[datetime] = None
    inspection_period_days: Optional[int] = Field(None, ge=0, le=30)
    financing_contingency_days: Optional[int] = Field(None, ge=0, le=60)
    earnest_money: Optional[float] = Field(None, ge=0)
    additional_terms: Optional[str] = Field(None, max_length=2000)
    expiration_date: Optional[datetime] = None

class PurchaseOfferReview(BaseModel):
    status: OfferStatus
    review_notes: Optional[str] = Field(None, max_length=1000)
    counter_offer_price: Optional[float] = Field(None, gt=0)
    counter_offer_terms: Optional[str] = Field(None, max_length=2000)

class PurchaseOfferOut(PurchaseOfferBase):
    id: int
    buyer_id: int
    status: OfferStatus
    counter_offer_price: Optional[float] = None
    counter_offer_terms: Optional[str] = None
    counter_offer_date: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Booking Summary Schemas
class BookingSummary(BaseModel):
    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    upcoming_bookings: List[PropertyBookingOut]

class ApplicationSummary(BaseModel):
    total_applications: int
    pending_applications: int
    approved_applications: int
    rejected_applications: int
    recent_applications: List[RentalApplicationOut]

class OfferSummary(BaseModel):
    total_offers: int
    pending_offers: int
    accepted_offers: int
    rejected_offers: int
    recent_offers: List[PurchaseOfferOut]

# Booking Analytics
class BookingAnalytics(BaseModel):
    property_id: int
    total_views: int
    total_bookings: int
    conversion_rate: float
    average_booking_duration: int
    popular_time_slots: List[Dict[str, Any]]
    booking_trends: List[Dict[str, Any]]

# Notification Schemas
class BookingNotification(BaseModel):
    booking_id: int
    notification_type: str  # 'created', 'confirmed', 'cancelled', 'reminder'
    recipient_id: int
    message: str
    scheduled_for: Optional[datetime] = None

class ApplicationNotification(BaseModel):
    application_id: int
    notification_type: str  # 'submitted', 'reviewed', 'approved', 'rejected'
    recipient_id: int
    message: str

class OfferNotification(BaseModel):
    offer_id: int
    notification_type: str  # 'submitted', 'reviewed', 'accepted', 'rejected', 'counter_offered'
    recipient_id: int
    message: str
