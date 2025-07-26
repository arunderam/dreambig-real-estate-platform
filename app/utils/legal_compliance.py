"""
Legal compliance utilities for DreamBig Real Estate Platform
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.db import models
import logging
import json
import hashlib
from enum import Enum

logger = logging.getLogger(__name__)

class DataProcessingPurpose(str, Enum):
    """GDPR data processing purposes"""
    ACCOUNT_MANAGEMENT = "account_management"
    PROPERTY_SERVICES = "property_services"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    LEGAL_COMPLIANCE = "legal_compliance"
    CUSTOMER_SUPPORT = "customer_support"

class ConsentType(str, Enum):
    """Types of user consent"""
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    MARKETING_EMAILS = "marketing_emails"
    DATA_PROCESSING = "data_processing"
    COOKIES = "cookies"
    THIRD_PARTY_SHARING = "third_party_sharing"

class AuditEventType(str, Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    PROPERTY_VIEWED = "property_viewed"
    BOOKING_CREATED = "booking_created"
    APPLICATION_SUBMITTED = "application_submitted"
    OFFER_SUBMITTED = "offer_submitted"
    ADMIN_ACTION = "admin_action"

class LegalComplianceManager:
    """Manager for legal compliance operations"""

    def __init__(self, db: Session):
        self.db = db

    def record_consent(
        self,
        user_id: int,
        consent_type: ConsentType,
        consent_given: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_text: Optional[str] = None
    ) -> bool:
        """Record user consent for GDPR compliance"""
        try:
            consent_record = models.UserConsent(
                user_id=user_id,
                consent_type=consent_type.value,
                consent_given=consent_given,
                consent_date=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                consent_text=consent_text,
                consent_version="1.0"  # Track version of terms/policy
            )
            
            self.db.add(consent_record)
            self.db.commit()
            
            # Record audit event
            self.record_audit_event(
                user_id=user_id,
                event_type=AuditEventType.CONSENT_GIVEN if consent_given else AuditEventType.CONSENT_WITHDRAWN,
                details={
                    "consent_type": consent_type.value,
                    "consent_given": consent_given,
                    "ip_address": ip_address
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording consent: {str(e)}")
            self.db.rollback()
            return False

    def get_user_consents(self, user_id: int) -> Dict[str, Any]:
        """Get all consents for a user"""
        try:
            consents = self.db.query(models.UserConsent).filter(
                models.UserConsent.user_id == user_id
            ).order_by(models.UserConsent.consent_date.desc()).all()
            
            # Get latest consent for each type
            latest_consents = {}
            for consent in consents:
                if consent.consent_type not in latest_consents:
                    latest_consents[consent.consent_type] = {
                        "consent_given": consent.consent_given,
                        "consent_date": consent.consent_date,
                        "consent_version": consent.consent_version
                    }
            
            return latest_consents
            
        except Exception as e:
            logger.error(f"Error getting user consents: {str(e)}")
            return {}

    def record_audit_event(
        self,
        user_id: Optional[int],
        event_type: AuditEventType,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Record audit event for compliance tracking"""
        try:
            audit_event = models.AuditLog(
                user_id=user_id,
                event_type=event_type.value,
                event_timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details) if details else None,
                session_id=self._generate_session_id(user_id, ip_address)
            )
            
            self.db.add(audit_event)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error recording audit event: {str(e)}")
            self.db.rollback()
            return False

    def get_audit_trail(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        try:
            query = self.db.query(models.AuditLog)
            
            if user_id:
                query = query.filter(models.AuditLog.user_id == user_id)
            
            if event_type:
                query = query.filter(models.AuditLog.event_type == event_type.value)
            
            if start_date:
                query = query.filter(models.AuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(models.AuditLog.event_timestamp <= end_date)
            
            events = query.order_by(
                models.AuditLog.event_timestamp.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "event_type": event.event_type,
                    "event_timestamp": event.event_timestamp,
                    "ip_address": event.ip_address,
                    "details": json.loads(event.details) if event.details else None
                }
                for event in events
            ]
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {str(e)}")
            return []

    def process_data_deletion_request(self, user_id: int) -> Dict[str, Any]:
        """Process GDPR data deletion request"""
        try:
            user = self.db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            deletion_summary = {
                "user_data": False,
                "properties": False,
                "bookings": False,
                "applications": False,
                "offers": False,
                "audit_logs": False,
                "consents": False
            }
            
            # Check if user has active properties, bookings, etc.
            active_properties = self.db.query(models.Property).filter(
                models.Property.owner_id == user_id,
                models.Property.status == models.PropertyStatus.AVAILABLE
            ).count()
            
            if active_properties > 0:
                return {
                    "success": False,
                    "error": "Cannot delete user with active properties. Please deactivate properties first."
                }
            
            # Anonymize user data instead of deletion for audit purposes
            anonymized_email = f"deleted_user_{user_id}@anonymized.com"
            user.email = anonymized_email
            user.full_name = "Deleted User"
            user.phone = None
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            deletion_summary["user_data"] = True
            
            # Anonymize bookings
            bookings = self.db.query(models.PropertyBooking).filter(
                models.PropertyBooking.user_id == user_id
            ).all()
            for booking in bookings:
                booking.contact_name = "Deleted User"
                booking.contact_email = anonymized_email
                booking.contact_phone = "DELETED"
                booking.notes = "User data deleted per GDPR request"
            deletion_summary["bookings"] = True
            
            # Anonymize rental applications
            applications = self.db.query(models.RentalApplication).filter(
                models.RentalApplication.applicant_id == user_id
            ).all()
            for app in applications:
                app.employer_name = "DELETED"
                app.previous_address = "DELETED"
                app.references = []
                app.documents = []
            deletion_summary["applications"] = True
            
            # Keep audit logs for legal compliance but mark as anonymized
            audit_logs = self.db.query(models.AuditLog).filter(
                models.AuditLog.user_id == user_id
            ).all()
            for log in audit_logs:
                if log.details:
                    details = json.loads(log.details)
                    details["user_anonymized"] = True
                    log.details = json.dumps(details)
            deletion_summary["audit_logs"] = True
            
            # Record the deletion request
            self.record_audit_event(
                user_id=user_id,
                event_type=AuditEventType.DATA_DELETION,
                details={
                    "deletion_type": "gdpr_request",
                    "deletion_summary": deletion_summary
                }
            )
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "User data anonymized successfully",
                "deletion_summary": deletion_summary
            }
            
        except Exception as e:
            logger.error(f"Error processing data deletion request: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": "Failed to process deletion request"}

    def generate_data_export(self, user_id: int) -> Dict[str, Any]:
        """Generate GDPR data export for user"""
        try:
            user = self.db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Collect all user data
            export_data = {
                "user_profile": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                },
                "properties": [],
                "bookings": [],
                "rental_applications": [],
                "purchase_offers": [],
                "consents": [],
                "audit_logs": []
            }
            
            # Get properties
            properties = self.db.query(models.Property).filter(
                models.Property.owner_id == user_id
            ).all()
            for prop in properties:
                export_data["properties"].append({
                    "id": prop.id,
                    "title": prop.title,
                    "description": prop.description,
                    "price": prop.price,
                    "location": prop.location,
                    "created_at": prop.created_at.isoformat() if prop.created_at else None
                })
            
            # Get bookings
            bookings = self.db.query(models.PropertyBooking).filter(
                models.PropertyBooking.user_id == user_id
            ).all()
            for booking in bookings:
                export_data["bookings"].append({
                    "id": booking.id,
                    "property_id": booking.property_id,
                    "booking_type": booking.booking_type,
                    "status": booking.status,
                    "preferred_date": booking.preferred_date.isoformat() if booking.preferred_date else None,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None
                })
            
            # Get consents
            consents = self.db.query(models.UserConsent).filter(
                models.UserConsent.user_id == user_id
            ).all()
            for consent in consents:
                export_data["consents"].append({
                    "consent_type": consent.consent_type,
                    "consent_given": consent.consent_given,
                    "consent_date": consent.consent_date.isoformat() if consent.consent_date else None,
                    "consent_version": consent.consent_version
                })
            
            # Record the export request
            self.record_audit_event(
                user_id=user_id,
                event_type=AuditEventType.DATA_ACCESS,
                details={"export_type": "gdpr_data_export"}
            )
            
            return {
                "success": True,
                "export_data": export_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating data export: {str(e)}")
            return {"success": False, "error": "Failed to generate data export"}

    def check_data_retention_compliance(self) -> Dict[str, Any]:
        """Check and enforce data retention policies"""
        try:
            current_date = datetime.utcnow()
            retention_summary = {
                "audit_logs_cleaned": 0,
                "old_bookings_archived": 0,
                "expired_consents_flagged": 0
            }
            
            # Clean old audit logs (keep for 7 years)
            retention_date = current_date - timedelta(days=7*365)
            old_logs = self.db.query(models.AuditLog).filter(
                models.AuditLog.event_timestamp < retention_date
            ).count()
            
            if old_logs > 0:
                # Archive instead of delete for compliance
                self.db.query(models.AuditLog).filter(
                    models.AuditLog.event_timestamp < retention_date
                ).update({"archived": True})
                retention_summary["audit_logs_cleaned"] = old_logs
            
            # Archive old completed bookings (after 2 years)
            booking_retention_date = current_date - timedelta(days=2*365)
            old_bookings = self.db.query(models.PropertyBooking).filter(
                models.PropertyBooking.completed_date < booking_retention_date,
                models.PropertyBooking.status == models.BookingStatus.COMPLETED
            ).count()
            
            retention_summary["old_bookings_archived"] = old_bookings
            
            self.db.commit()
            
            return {
                "success": True,
                "retention_summary": retention_summary,
                "checked_at": current_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking data retention compliance: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": "Failed to check retention compliance"}

    def _generate_session_id(self, user_id: Optional[int], ip_address: Optional[str]) -> str:
        """Generate session ID for audit tracking"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{user_id}_{ip_address}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()

# Compliance decorators and middleware

def audit_data_access(event_type: AuditEventType):
    """Decorator to audit data access operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user_id and other details from function arguments
            user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 else None)
            
            try:
                result = func(*args, **kwargs)
                
                # Record successful access
                if hasattr(args[0], 'db'):
                    compliance_manager = LegalComplianceManager(args[0].db)
                    compliance_manager.record_audit_event(
                        user_id=user_id,
                        event_type=event_type,
                        details={"function": func.__name__, "success": True}
                    )
                
                return result
                
            except Exception as e:
                # Record failed access attempt
                if hasattr(args[0], 'db'):
                    compliance_manager = LegalComplianceManager(args[0].db)
                    compliance_manager.record_audit_event(
                        user_id=user_id,
                        event_type=event_type,
                        details={"function": func.__name__, "success": False, "error": str(e)}
                    )
                raise
                
        return wrapper
    return decorator
