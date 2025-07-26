from sqlalchemy.orm import Session
from app.db import models
from typing import List, Optional, Dict
import json


def get_user(db:Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_firebase_uid(db:Session, firebase_uid: str):
    return db.query(models.User).filter(models.User.firebase_uid == firebase_uid).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.phone == phone).first()

def create_user(db: Session, user_data: dict):
    try:
        print(f"Creating user with data: {user_data}")  # Debug logging
        db_user = models.User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"User created successfully with ID: {db_user.id}")  # Debug logging
        return db_user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {str(e)}")  # Debug logging
        print(f"User data that failed: {user_data}")  # Debug logging
        raise e

def update_user_kyc(db: Session, user_id: int, kyc_details: dict):
    db_user = get_user(db, user_id=user_id)
    if db_user:
        db_user.kyc_details = json.dumps(kyc_details) # type: ignore
        db_user.kyc_verified = True # type: ignore
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: dict):
    try:
        print(f"Updating user {user_id} with data: {user_update}")  # Debug logging

        db_user = get_user(db, user_id=user_id)
        if not db_user:
            print(f"User {user_id} not found")
            return None

        # Update only the fields that are provided and exist on the model
        updated_fields = []
        for field, value in user_update.items():
            if hasattr(db_user, field) and value is not None:
                setattr(db_user, field, value)
                updated_fields.append(field)

        print(f"Updated fields: {updated_fields}")

        db.commit()
        db.refresh(db_user)
        print(f"User {user_id} updated successfully")
        return db_user

    except Exception as e:
        db.rollback()
        print(f"Error updating user {user_id}: {str(e)}")
        print(f"Update data that failed: {user_update}")
        raise e

#Property Operations
def create_property(db: Session, property_data: dict, owner_id: int):
    db_property = models.Property(**property_data, owner_id=owner_id)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

def get_property(db: Session, property_id: int):
    return db.query(models.Property).filter(models.Property.id == property_id).first()

def get_properties(db: Session, skip: int = 0, limit: int = 100, filters: Optional[Dict] = None):
    query = db.query(models.Property)
    if filters:
        if filters.get("price_min"):
            query = query.filter(models.Property.price>= filters["price_min"])
            
        if filters.get("price_max"):
            query = query.filter(models.Property.price<= filters["price_max"])
            
        if filters.get("bhk"):
            query = query.filter(models.Property.bhk == filters["bhk"])
            
        if filters.get("property_type"):
            query = query.filter(models.Property.property_type == filters["property_type"])
            
        if filters.get("furnishing"):
            query = query.filter(models.Property.furnishing == filters["furnishing"])

        if filters.get("city"):
            query = query.filter(models.Property.city.ilike(f"%{filters['city']}%"))

        if filters.get("verified_owner"):
            query = query.filter(models.Property.is_verified == filters["verified_owner"])
            
    return query.offset(skip).limit(limit).all()

def get_properties_by_owners(db: Session, owner_id: int, status: str):
    return db.query(models.Property).filter(
        models.Property.owner_id == owner_id,
        models.Property.status == status
    ).all()

def update_property(db: Session, property_id: int, status: str):
    db_property = get_property(db, property_id=property_id)
    if db_property:
        db_property.status = status  # type: ignore
        db.commit()
        db.refresh(db_property)
    return db_property

def add_property_image(db: Session, property_id: int, image_urls: List[str]):
    db_property = get_property(db, property_id=property_id)
    if not db_property:
        return None

    images = []
    for url in image_urls:
        db_image = models.PropertyImage(url=url, property_id=property_id)
        db.add(db_image)
        images.append(db_image)

    db.commit()
    return images

def add_property_video(db: Session, property_id: int, video_urls: List[str], titles: Optional[List[str]] = None, descriptions: Optional[List[str]] = None):
    db_property = get_property(db, property_id=property_id)
    if not db_property:
        return None

    videos = []
    for i, url in enumerate(video_urls):
        title = titles[i] if titles and i < len(titles) else None
        description = descriptions[i] if descriptions and i < len(descriptions) else None

        db_video = models.PropertyVideo(
            url=url,
            property_id=property_id,
            title=title,
            description=description
        )
        db.add(db_video)
        videos.append(db_video)

    db.commit()
    return videos

# Favorite operations

def add_favorite(db: Session, user_id: int, property_id: int):
    db_favorite = models.Favorite(user_id=user_id, property_id=property_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite

def get_favorites(db: Session, user_id: int):
    return db.query(models.Favorite).filter(models.Favorite.user_id == user_id).all()

# Alias for backward compatibility
def get_user_favorites(db: Session, user_id: int):
    return get_favorites(db, user_id)

def remove_favorite(db: Session, user_id: int, property_id: int):
    db_favorite = db.query(models.Favorite).filter(models.Favorite.user_id==user_id, models.Favorite.property_id==property_id).first()
    if db_favorite:
        db.delete(db_favorite)
        db.commit()
        return True
    return False


# Recently Viewed Properties

def add_recently_viewed(db: Session, user_id: int, property_id: int):
    db_viewed = models.RecentlyViewed(user_id=user_id, property_id=property_id)
    db.add(db_viewed)
    db.commit()
    db.refresh(db_viewed)
    return db_viewed


def get_recently_viewed(db: Session, user_id: int, limit: int = 5):
    return db.query(models.RecentlyViewed).filter(models.RecentlyViewed.user_id == user_id).order_by(models.RecentlyViewed.id.desc()).limit(limit).all()

# Investment operations
def create_investment(db: Session, investment_data: dict, investor_id: int):
    try:
        print(f"Creating investment with data: {investment_data}")  # Debug logging

        # Remove investor_id from investment_data if it exists to avoid duplicate
        investment_data_clean = investment_data.copy()
        if 'investor_id' in investment_data_clean:
            investment_data_clean.pop('investor_id')

        db_investment = models.Investment(**investment_data_clean, investor_id=investor_id)
        db.add(db_investment)
        db.commit()
        db.refresh(db_investment)
        print(f"Investment created successfully with ID: {db_investment.id}")
        return db_investment

    except Exception as e:
        db.rollback()
        print(f"Error creating investment: {str(e)}")
        print(f"Investment data that failed: {investment_data}")
        raise e

def get_investments(db: Session, investment_id: int):
    return db.query(models.Investment).filter(models.Investment.id == investment_id).first()

def get_investments_by_user(db: Session, user_id: int):
    return db.query(models.Investment).filter(models.Investment.investor_id == user_id).all()

def add_investment_document(db: Session, investment_id: int, name:str, url: str):
    db_document = models.InvestmentDocument(investment_id=investment_id, name=name, url=url)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

# Service Provider Operations
def get_service_provider(db: Session, provider_id: int):
    return db.query(models.ServiceProvider).filter(models.ServiceProvider.id == provider_id).first()

def get_service_providers(db: Session, skip: int = 0, limit: int = 100, service_type: Optional[str] = None):
    query = db.query(models.ServiceProvider)
    if service_type:
        query = query.filter(models.ServiceProvider.service_type == service_type)
    return query.offset(skip).limit(limit).all()

def create_service_provider(db: Session, provider_data: dict):
    db_provider = models.ServiceProvider(**provider_data)
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider

# Service Booking Operations
def get_service_booking(db: Session, booking_id: int):
    return db.query(models.ServiceBooking).filter(models.ServiceBooking.id == booking_id).first()

def get_service_bookings_by_user(db: Session, user_id: int, status: Optional[str] = None):
    query = db.query(models.ServiceBooking).filter(models.ServiceBooking.user_id == user_id)
    if status:
        query = query.filter(models.ServiceBooking.status == status)
    return query.order_by(models.ServiceBooking.created_at.desc()).all()

def create_service_booking(db: Session, booking_data: dict):
    db_booking = models.ServiceBooking(**booking_data)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

# Notifications operations
def create_notification(db: Session, notification_data: dict):
    db_notification = models.Notification(**notification_data)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_user_notifications(db: Session, user_id: int, is_read: Optional[bool] = None):
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if is_read is not None:
        query = query.filter(models.Notification.is_read == is_read)
    return query.all()

def mark_notification_as_read(db: Session, notification_id: int):
    db_notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if db_notification:
        db_notification.is_read = True  # type: ignore
        db.commit()
        db.refresh(db_notification)
    return db_notification

# Chat CRUD operations
def create_chat_room(db: Session, room_data: dict):
    """Create a new chat room"""
    db_room = models.ChatRoom(**room_data)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_chat_room(db: Session, room_id: str):
    """Get chat room by ID"""
    return db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()

def get_user_chat_rooms(db: Session, user_id: int):
    """Get all chat rooms for a user"""
    return db.query(models.ChatRoom).join(models.ChatParticipant).filter(
        models.ChatParticipant.user_id == user_id,
        models.ChatParticipant.is_active == True
    ).all()

def create_chat_message(db: Session, message_data: dict):
    """Create a new chat message"""
    db_message = models.ChatMessage(**message_data)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_messages(db: Session, room_id: str, limit: int = 50, offset: int = 0):
    """Get chat messages for a room"""
    return db.query(models.ChatMessage).filter(
        models.ChatMessage.room_id == room_id,
        models.ChatMessage.is_deleted == False
    ).order_by(models.ChatMessage.timestamp.desc()).offset(offset).limit(limit).all()

def add_chat_participant(db: Session, room_id: str, user_id: int, role: str = "participant"):
    """Add participant to chat room"""
    # Check if already exists
    existing = db.query(models.ChatParticipant).filter(
        models.ChatParticipant.room_id == room_id,
        models.ChatParticipant.user_id == user_id
    ).first()

    if existing:
        existing.is_active = True  # type: ignore
        existing.role = role  # type: ignore
        db.commit()
        db.refresh(existing)
        return existing

    db_participant = models.ChatParticipant(
        room_id=room_id,
        user_id=user_id,
        role=role
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

def remove_chat_participant(db: Session, room_id: str, user_id: int):
    """Remove participant from chat room"""
    participant = db.query(models.ChatParticipant).filter(
        models.ChatParticipant.room_id == room_id,
        models.ChatParticipant.user_id == user_id
    ).first()

    if participant:
        participant.is_active = False  # type: ignore
        db.commit()
        db.refresh(participant)
    return participant

def get_chat_participants(db: Session, room_id: str):
    """Get all participants in a chat room"""
    return db.query(models.ChatParticipant).filter(
        models.ChatParticipant.room_id == room_id,
        models.ChatParticipant.is_active == True
    ).all()

def update_last_read(db: Session, room_id: str, user_id: int):
    """Update user's last read timestamp for a room"""
    participant = db.query(models.ChatParticipant).filter(
        models.ChatParticipant.room_id == room_id,
        models.ChatParticipant.user_id == user_id
    ).first()

    if participant:
        from datetime import datetime, timezone
        participant.last_read_at = datetime.now(timezone.utc)  # type: ignore
        db.commit()
        db.refresh(participant)
    return participant


# Property search function
def search_properties(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bhk: Optional[int] = None,
    property_type: Optional[str] = None,
    **kwargs
):
    """Search properties with various filters"""
    query = db.query(models.Property)

    # Apply filters
    if city:
        query = query.filter(models.Property.city.ilike(f"%{city}%"))

    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)

    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)

    if bhk is not None:
        query = query.filter(models.Property.bhk == bhk)

    if property_type:
        query = query.filter(models.Property.property_type.ilike(f"%{property_type}%"))

    # Apply pagination
    return query.offset(skip).limit(limit).all()