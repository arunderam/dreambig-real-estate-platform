from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional
from app.db.models import InvestmentRiskLevel

class InvestmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    expected_roi: float = Field(..., gt=0, le=100)
    risk_level: InvestmentRiskLevel
    investment_type: str = Field(..., min_length=1, max_length=50)
    duration_months: int = Field(..., gt=0, le=360)
    description: Optional[str] = None
    location: Optional[str] = None

class InvestmentCreate(InvestmentBase):
    property_id: Optional[int] = None  # Optional for general investments

class InvestmentOut(InvestmentBase):
    id: int
    investor_id: int
    property_id: Optional[int] = None
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InvestmentDocument(BaseModel):
    id: int
    name: str
    url: HttpUrl

    class Config:
        from_attributes = True