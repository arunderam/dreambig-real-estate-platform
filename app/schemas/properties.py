from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime
from app.db.models import PropertyType, FurnishingType, PropertyStatus

class PropertyBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=2000)
    price: float = Field(..., gt=0)
    bhk: int = Field(..., ge=0)
    area: float = Field(..., gt=0)
    property_type: PropertyType
    furnishing: FurnishingType
    address: str = Field(..., max_length=200)
    city: str = Field(..., max_length=50)
    state: str = Field(..., max_length=50)
    pincode: str = Field(..., min_length=6, max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    status: Optional[PropertyStatus] = None

class PropertyOut(PropertyBase):
    id: int
    status: PropertyStatus
    owner_id: int
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PropertyImage(BaseModel):
    id: int
    url: HttpUrl

    class Config:
        from_attributes = True

class PropertyVideo(BaseModel):
    id: int
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class PropertyFeature(BaseModel):
    id: int
    name: str
    value: str

    class Config:
        from_attributes = True