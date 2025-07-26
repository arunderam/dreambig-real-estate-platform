from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.utils.legal_compliance import (
    LegalComplianceManager, ConsentType, AuditEventType
)
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic schemas for legal compliance

class ConsentRequest(BaseModel):
    consent_type: ConsentType
    consent_given: bool
    consent_text: Optional[str] = None

class ConsentResponse(BaseModel):
    consent_type: str
    consent_given: bool
    consent_date: datetime
    consent_version: str

class DataExportRequest(BaseModel):
    export_format: str = Field(default="json", pattern="^(json|csv)$")

class DataDeletionRequest(BaseModel):
    confirmation: bool = Field(..., description="Must be true to confirm deletion")
    reason: Optional[str] = Field(None, max_length=500)

class AuditEventResponse(BaseModel):
    id: int
    user_id: Optional[int]
    event_type: str
    event_timestamp: datetime
    ip_address: Optional[str]
    details: Optional[Dict[str, Any]]

# Consent Management Endpoints

@router.post("/consent", response_model=Dict[str, str])
async def record_user_consent(
    consent_request: ConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Record user consent for GDPR compliance"""
    try:
        compliance_manager = LegalComplianceManager(db)
        
        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        success = compliance_manager.record_consent(
            user_id=getattr(current_user, 'id'),
            consent_type=consent_request.consent_type,
            consent_given=consent_request.consent_given,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text=consent_request.consent_text
        )
        
        if success:
            return {
                "message": f"Consent for {consent_request.consent_type} recorded successfully",
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record consent"
            )
            
    except Exception as e:
        logger.error(f"Error recording consent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent"
        )

@router.get("/consent", response_model=Dict[str, ConsentResponse])
async def get_user_consents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all consents for current user"""
    try:
        compliance_manager = LegalComplianceManager(db)
        consents = compliance_manager.get_user_consents(getattr(current_user, 'id'))
        
        # Convert to response format
        response = {}
        for consent_type, consent_data in consents.items():
            response[consent_type] = ConsentResponse(
                consent_type=consent_type,
                consent_given=consent_data["consent_given"],
                consent_date=consent_data["consent_date"],
                consent_version=consent_data["consent_version"]
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting user consents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consents"
        )

# Data Rights Endpoints (GDPR)

@router.post("/data-export")
async def request_data_export(
    export_request: DataExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Request data export (GDPR Article 20 - Right to data portability)"""
    try:
        compliance_manager = LegalComplianceManager(db)
        
        # Generate data export
        export_result = compliance_manager.generate_data_export(getattr(current_user, 'id'))
        
        if export_result["success"]:
            # In a real implementation, you would:
            # 1. Generate the export file
            # 2. Store it securely
            # 3. Send download link via email
            # 4. Schedule automatic deletion after 30 days
            
            return {
                "message": "Data export generated successfully",
                "export_id": f"export_{getattr(current_user, 'id')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed",
                "download_expires_at": (datetime.utcnow().isoformat() + "Z"),
                "data": export_result["export_data"]  # In production, this would be a download link
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=export_result["error"]
            )
            
    except Exception as e:
        logger.error(f"Error generating data export: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate data export"
        )

@router.post("/data-deletion")
async def request_data_deletion(
    deletion_request: DataDeletionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Request data deletion (GDPR Article 17 - Right to erasure)"""
    try:
        if not deletion_request.confirmation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required for data deletion"
            )
        
        compliance_manager = LegalComplianceManager(db)
        
        # Record the deletion request in audit log first
        ip_address = request.client.host if request.client else None
        compliance_manager.record_audit_event(
            user_id=getattr(current_user, 'id'),
            event_type=AuditEventType.DATA_DELETION,
            details={
                "deletion_requested": True,
                "reason": deletion_request.reason,
                "ip_address": ip_address
            },
            ip_address=ip_address
        )
        
        # Process deletion
        deletion_result = compliance_manager.process_data_deletion_request(getattr(current_user, 'id'))
        
        if deletion_result["success"]:
            return {
                "message": "Data deletion processed successfully",
                "status": "completed",
                "deletion_summary": deletion_result["deletion_summary"],
                "note": "Your account has been anonymized. Some data may be retained for legal compliance."
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=deletion_result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data deletion request"
        )

# Audit and Transparency Endpoints

@router.get("/audit-trail", response_model=List[AuditEventResponse])
async def get_user_audit_trail(
    limit: int = 50,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get audit trail for current user"""
    try:
        compliance_manager = LegalComplianceManager(db)
        
        audit_event_type = None
        if event_type:
            try:
                audit_event_type = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {event_type}"
                )
        
        events = compliance_manager.get_audit_trail(
            user_id=getattr(current_user, 'id'),
            event_type=audit_event_type,
            limit=min(limit, 100)  # Cap at 100 events
        )
        
        return [
            AuditEventResponse(
                id=event["id"],
                user_id=event["user_id"],
                event_type=event["event_type"],
                event_timestamp=event["event_timestamp"],
                ip_address=event["ip_address"],
                details=event["details"]
            )
            for event in events
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit trail"
        )

# Legal Documents Endpoints

@router.get("/terms-of-service")
async def get_terms_of_service(db: Session = Depends(get_db)):
    """Get current terms of service"""
    try:
        # In a real implementation, this would fetch from legal_documents table
        return {
            "document_type": "terms_of_service",
            "version": "1.0",
            "effective_date": "2024-01-01T00:00:00Z",
            "title": "DreamBig Real Estate Platform - Terms of Service",
            "content": """
            # Terms of Service

            ## 1. Acceptance of Terms
            By accessing and using DreamBig Real Estate Platform, you accept and agree to be bound by the terms and provision of this agreement.

            ## 2. Use License
            Permission is granted to temporarily download one copy of the materials on DreamBig's website for personal, non-commercial transitory viewing only.

            ## 3. Disclaimer
            The materials on DreamBig's website are provided on an 'as is' basis. DreamBig makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.

            ## 4. Limitations
            In no event shall DreamBig or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on DreamBig's website.

            ## 5. Privacy Policy
            Your privacy is important to us. Please review our Privacy Policy, which also governs your use of the website.

            ## 6. Contact Information
            If you have any questions about these Terms of Service, please contact us at legal@dreambig.com.
            """
        }
        
    except Exception as e:
        logger.error(f"Error getting terms of service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve terms of service"
        )

@router.get("/privacy-policy")
async def get_privacy_policy(db: Session = Depends(get_db)):
    """Get current privacy policy"""
    try:
        return {
            "document_type": "privacy_policy",
            "version": "1.0",
            "effective_date": "2024-01-01T00:00:00Z",
            "title": "DreamBig Real Estate Platform - Privacy Policy",
            "content": """
            # Privacy Policy

            ## 1. Information We Collect
            We collect information you provide directly to us, such as when you create an account, make a booking, or contact us for support.

            ## 2. How We Use Your Information
            We use the information we collect to provide, maintain, and improve our services, process transactions, and communicate with you.

            ## 3. Information Sharing
            We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy.

            ## 4. Data Security
            We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.

            ## 5. Your Rights
            You have the right to access, update, or delete your personal information. You may also object to certain processing of your data.

            ## 6. Contact Us
            If you have questions about this Privacy Policy, please contact us at privacy@dreambig.com.
            """
        }
        
    except Exception as e:
        logger.error(f"Error getting privacy policy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve privacy policy"
        )
