# This makes the schemas available as a package
from .users import UserBase, UserCreate, UserUpdate, UserInDB
from .properties import (
    PropertyBase,
    PropertyCreate,
    PropertyUpdate,
    PropertyOut,
    PropertyImage,
    PropertyVideo,
    PropertyFeature
)
from .investments import (
    InvestmentBase,
    InvestmentCreate,
    InvestmentOut,
    InvestmentDocument
)
from .services import (
    ServiceProviderBase,
    ServiceProviderCreate,
    ServiceProviderOut,
    ServiceBookingBase,
    ServiceBookingCreate,
    ServiceBookingOut
)
from .bookings import (
    PropertyBookingBase,
    PropertyBookingCreate,
    PropertyBookingUpdate,
    PropertyBookingStatusUpdate,
    PropertyBookingOut,
    RentalApplicationBase,
    RentalApplicationCreate,
    RentalApplicationUpdate,
    RentalApplicationReview,
    RentalApplicationOut,
    PurchaseOfferBase,
    PurchaseOfferCreate,
    PurchaseOfferUpdate,
    PurchaseOfferReview,
    PurchaseOfferOut,
    BookingSummary,
    ApplicationSummary,
    OfferSummary,
    BookingAnalytics
)

__all__ = [
    'UserBase', 'UserCreate', 'UserUpdate', 'UserInDB',
    'PropertyBase', 'PropertyCreate', 'PropertyUpdate', 'PropertyOut',
    'PropertyImage', 'PropertyVideo', 'PropertyFeature',
    'InvestmentBase', 'InvestmentCreate', 'InvestmentOut', 'InvestmentDocument',
    'ServiceProviderBase', 'ServiceProviderCreate', 'ServiceProviderOut',
    'ServiceBookingBase', 'ServiceBookingCreate', 'ServiceBookingOut',
    'PropertyBookingBase', 'PropertyBookingCreate', 'PropertyBookingUpdate',
    'PropertyBookingStatusUpdate', 'PropertyBookingOut',
    'RentalApplicationBase', 'RentalApplicationCreate', 'RentalApplicationUpdate',
    'RentalApplicationReview', 'RentalApplicationOut',
    'PurchaseOfferBase', 'PurchaseOfferCreate', 'PurchaseOfferUpdate',
    'PurchaseOfferReview', 'PurchaseOfferOut',
    'BookingSummary', 'ApplicationSummary', 'OfferSummary', 'BookingAnalytics'
]