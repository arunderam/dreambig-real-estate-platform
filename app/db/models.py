from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, JSON, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum

class UserRole(str, enum.Enum):
    TENANT = "tenant"
    OWNER = "owner"
    SERVICE_PROVIDER = "service_provider"
    INVESTOR = "investor"
    ADMIN = "admin"

class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    PLOT = "plot"
    COMMERCIAL = "commercial"

class FurnishingType(str, enum.Enum):
    FURNISHED = "furnished"
    SEMI_FURNISHED = "semi_furnished"
    UNFURNISHED = "unfurnished"

class PropertyStatus(str, enum.Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    RENTED = "rented"
    SOLD = "sold"

class InvestmentRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BookingType(str, enum.Enum):
    VIEWING = "viewing"
    RENTAL_APPLICATION = "rental_application"
    PURCHASE_OFFER = "purchase_offer"
    INSPECTION = "inspection"

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class OfferStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTER_OFFERED = "counter_offered"
    WITHDRAWN = "withdrawn"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)  # Allow NULL phone numbers
    name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.TENANT)
    is_active = Column(Boolean, default=True)
    kyc_verified = Column(Boolean, default=False)
    kyc_details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relationships
    properties = relationship("Property", back_populates="owner")
    favorites = relationship("Favorite", back_populates="user")
    recently_viewed = relationship("RecentlyViewed", back_populates="user")
    investments = relationship("Investment", back_populates="investor")
    service_bookings = relationship("ServiceBooking", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    sent_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id")
    chat_participations = relationship("ChatParticipant", back_populates="user")

    # Booking system relationships
    property_bookings = relationship("PropertyBooking", foreign_keys="PropertyBooking.user_id")
    rental_applications = relationship("RentalApplication", foreign_keys="RentalApplication.applicant_id")
    purchase_offers = relationship("PurchaseOffer", foreign_keys="PurchaseOffer.buyer_id")

    # Legal compliance relationships
    consents = relationship("UserConsent")
    audit_logs = relationship("AuditLog")

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    price = Column(Float)
    bhk = Column(Integer)
    area = Column(Float)
    property_type = Column(Enum(PropertyType))
    furnishing = Column(Enum(FurnishingType))
    address = Column(String)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE)
    is_verified = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property")
    videos = relationship("PropertyVideo", back_populates="property")
    features = relationship("PropertyFeature", back_populates="property")
    favorites = relationship("Favorite", back_populates="property")
    recently_viewed = relationship("RecentlyViewed", back_populates="property")
    investments = relationship("Investment", back_populates="property")

    # Booking system relationships
    property_bookings = relationship("PropertyBooking")
    rental_applications = relationship("RentalApplication")
    purchase_offers = relationship("PurchaseOffer")

class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    property_id = Column(Integer, ForeignKey("properties.id"))

    property = relationship("Property", back_populates="images")

class PropertyVideo(Base):
    __tablename__ = "property_videos"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"))

    property = relationship("Property", back_populates="videos")

class PropertyFeature(Base):
    __tablename__ = "property_features"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    value = Column(String)
    property_id = Column(Integer, ForeignKey("properties.id"))

    property = relationship("Property", back_populates="features")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")

class RecentlyViewed(Base):
    __tablename__ = "recently_viewed"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recently_viewed")
    property = relationship("Property", back_populates="recently_viewed")

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float)
    expected_roi = Column(Float)
    risk_level = Column(Enum(InvestmentRiskLevel))
    investment_type = Column(String)  # property, rental, development, reit, commercial
    duration_months = Column(Integer)
    description = Column(Text)
    location = Column(String)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    status = Column(String, default="active")
    investor_id = Column(Integer, ForeignKey("users.id"))
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)  # Optional for general investments
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    investor = relationship("User", back_populates="investments")
    property = relationship("Property", back_populates="investments")
    documents = relationship("InvestmentDocument", back_populates="investment")

class InvestmentDocument(Base):
    __tablename__ = "investment_documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    url = Column(String)
    investment_id = Column(Integer, ForeignKey("investments.id"))

    investment = relationship("Investment", back_populates="documents")

class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    service_type = Column(String)
    description = Column(String)
    contact_number = Column(String)
    email = Column(String)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    service_bookings = relationship("ServiceBooking", back_populates="service_provider")

class ServiceBooking(Base):
    __tablename__ = "service_bookings"

    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String)
    details = Column(JSON)
    status = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_provider_id = Column(Integer, ForeignKey("service_providers.id"))
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="service_bookings")
    service_provider = relationship("ServiceProvider", back_populates="service_bookings")
    property = relationship("Property")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    type = Column(String)
    reference_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True, index=True)  # UUID or custom ID
    name = Column(String)
    description = Column(String)
    room_type = Column(String)  # 'property', 'service', 'investment', 'general'
    reference_id = Column(Integer)  # ID of related property/service/investment
    created_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    participants = relationship("ChatParticipant", back_populates="room", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("chat_rooms.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    message_type = Column(String, default="text")  # 'text', 'image', 'file', 'system'
    file_url = Column(String)  # For file/image messages
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    edited_at = Column(DateTime(timezone=True))

    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="participant")  # 'admin', 'moderator', 'participant'
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_read_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationships
    room = relationship("ChatRoom", back_populates="participants")
    user = relationship("User")

    # Unique constraint
    __table_args__ = (UniqueConstraint('room_id', 'user_id', name='unique_room_participant'),)

# Property Booking System Models

class PropertyBooking(Base):
    __tablename__ = "property_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_type = Column(Enum(BookingType))
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    property_id = Column(Integer, ForeignKey("properties.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Booking details
    preferred_date = Column(DateTime(timezone=True))
    preferred_time = Column(String)  # "10:00", "14:30", etc.
    duration_minutes = Column(Integer, default=60)
    notes = Column(Text)
    special_requirements = Column(Text)

    # Contact information
    contact_name = Column(String)
    contact_phone = Column(String)
    contact_email = Column(String)

    # Status tracking
    confirmed_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property")
    user = relationship("User")

class RentalApplication(Base):
    __tablename__ = "rental_applications"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    applicant_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED)

    # Application details
    desired_move_in_date = Column(DateTime(timezone=True))
    lease_duration_months = Column(Integer)
    offered_rent = Column(Float)
    security_deposit = Column(Float)

    # Applicant information
    employment_status = Column(String)
    employer_name = Column(String)
    monthly_income = Column(Float)
    previous_address = Column(Text)
    references = Column(JSON)  # List of references

    # Documents
    documents = Column(JSON)  # List of document URLs
    background_check_consent = Column(Boolean, default=False)

    # Review details
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property")
    applicant = relationship("User", foreign_keys=[applicant_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class PurchaseOffer(Base):
    __tablename__ = "purchase_offers"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(OfferStatus), default=OfferStatus.SUBMITTED)

    # Offer details
    offered_price = Column(Float)
    financing_type = Column(String)  # 'cash', 'mortgage', 'mixed'
    down_payment = Column(Float)
    loan_amount = Column(Float)
    contingencies = Column(JSON)  # List of contingencies

    # Timeline
    closing_date = Column(DateTime(timezone=True))
    inspection_period_days = Column(Integer, default=7)
    financing_contingency_days = Column(Integer, default=30)

    # Additional terms
    earnest_money = Column(Float)
    additional_terms = Column(Text)
    expiration_date = Column(DateTime(timezone=True))

    # Counter offer details
    counter_offer_price = Column(Float, nullable=True)
    counter_offer_terms = Column(Text, nullable=True)
    counter_offer_date = Column(DateTime(timezone=True), nullable=True)

    # Review details
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property")
    buyer = relationship("User", foreign_keys=[buyer_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

# Legal Compliance Models

class UserConsent(Base):
    __tablename__ = "user_consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    consent_type = Column(String(50))  # terms_of_service, privacy_policy, marketing_emails, etc.
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True), server_default=func.now())
    consent_version = Column(String(20))  # Version of terms/policy
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    consent_text = Column(Text)  # Full text of what user consented to
    withdrawn_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50))  # login, data_access, data_modification, etc.
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    details = Column(JSON)  # Additional event details
    archived = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")

class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(50))  # terms_of_service, privacy_policy, etc.
    version = Column(String(20))
    title = Column(String(255))
    content = Column(Text)
    effective_date = Column(DateTime(timezone=True))
    created_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User")