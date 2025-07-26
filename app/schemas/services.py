from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class ServiceProviderBase(BaseModel):
    name: str = Field(..., max_length=100)
    service_type: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    contact_number: str = Field(..., min_length=10, max_length=15)
    email: str = Field(..., max_length=100)

class ServiceProviderCreate(ServiceProviderBase):
    pass

class ServiceProviderOut(ServiceProviderBase):
    id: int
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ServiceBookingBase(BaseModel):
    service_type: str = Field(..., max_length=50)
    details: Dict[str, Any] = Field(default_factory=dict)

class ServiceBookingCreate(ServiceBookingBase):
    service_provider_id: int = Field(..., gt=0)
    property_id: Optional[int] = Field(None, gt=0)

class ServiceBookingOut(ServiceBookingBase):
    id: int
    user_id: int
    service_provider_id: int
    property_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True