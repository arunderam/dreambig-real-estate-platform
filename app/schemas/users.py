from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.db.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    name: str = Field(..., min_length=2, max_length=100)

class UserCreate(UserBase):
    firebase_uid: str = Field(..., min_length=20)
    role: UserRole = UserRole.TENANT

class UserUpdate(BaseModel):
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class UserInDB(UserBase):
    id: int
    firebase_uid: str
    role: UserRole
    is_active: bool
    kyc_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserRegistration(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.TENANT
    preferences: Optional[dict] = None
    location: Optional[str] = None

class UserPreferences(BaseModel):
    property_types: Optional[List[str]] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_locations: Optional[List[str]] = None
    bhk_preference: Optional[List[int]] = None
    furnishing_preference: Optional[List[str]] = None

class UserRegistrationResponse(BaseModel):
    user: UserInDB
    recommendations: Optional[List[dict]] = None
    fraud_score: Optional[dict] = None