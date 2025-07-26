from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from app.db import crud
from app.db.session import get_db
from app.schemas.investments import InvestmentCreate, InvestmentOut
from app.core.security import get_current_active_user
from typing import List

router = APIRouter()

@router.post("/", response_model=InvestmentOut)
async def create_investment(
    investment_data: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    # Allow any authenticated user to create investments (not just investors)
    # Users can invest regardless of their primary role

    # Verify the property exists if property_id is provided
    if investment_data.property_id:
        property = crud.get_property(db, property_id=investment_data.property_id)
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Prepare investment data
    investment_dict = investment_data.model_dump()
    investment_dict["investor_id"] = current_user.id # type: ignore

    # Calculate dates
    from datetime import datetime, timedelta
    start_date = datetime.now()
    end_date = start_date + timedelta(days=investment_data.duration_months * 30)

    investment_dict["start_date"] = start_date
    investment_dict["end_date"] = end_date
    investment_dict["status"] = "active"

    return crud.create_investment(
        db=db,
        investment_data=investment_dict,
        investor_id=current_user.id # type: ignore
    )

@router.get("/", response_model=List[InvestmentOut])
async def get_my_investments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    return crud.get_investments_by_user(db, user_id=current_user.id) # type: ignore

@router.get("/{investment_id}", response_model=InvestmentOut)
async def get_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    investment = crud.get_investment(db, investment_id=investment_id) # type: ignore
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    if investment.investor_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return investment