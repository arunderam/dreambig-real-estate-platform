from app.db import crud
from app.db.session import get_db
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import BackgroundTasks

from app.utils.email import send_email

async def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    reference_id: Optional[int] = None
):
    """Create and store a notification in database"""
    return crud.create_notification(
        db=db,
        notification_data={
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "reference_id": reference_id
        }
    )

async def send_property_alert(
    background_tasks: BackgroundTasks,
    db: Session,
    user_id: int,
    property_id: int
):
    """Send property alert notification"""
    notification = await create_notification(
        db=db,
        user_id=user_id,
        title="New Property Match",
        message="A property matching your criteria has been listed!",
        notification_type="property_alert",
        reference_id=property_id
    )
    
    # Also send email/SMS in background
    user = crud.get_user(db, user_id)
    if user and user.email: # type: ignore
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="New Property Match",
            body=f"A property matching your criteria has been listed (ID: {property_id})"
        ) # type: ignore

async def send_investment_update(
    background_tasks: BackgroundTasks,
    db: Session,
    investment_id: int,
    message: str
):
    """Send investment status update"""
    investment = crud.get_investment(db, investment_id) # type: ignore
    if not investment:
        return None
    
    notification = await create_notification(
        db=db,
        user_id=investment.investor_id,
        title="Investment Update",
        message=message,
        notification_type="investment_update",
        reference_id=investment_id
    )
    
    # Also send email
    user = crud.get_user(db, investment.investor_id)
    if user and user.email: # type: ignore
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject="Investment Update",
            body=f"Update for investment {investment_id}: {message}"
        ) # type: ignore