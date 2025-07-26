"""
Email verification functionality
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.db import crud, models
from app.utils.email import send_verification_email

logger = logging.getLogger(__name__)

class EmailVerificationManager:
    """Manages email verification tokens and operations"""
    
    def __init__(self):
        self.token_expiry_hours = 48  # 48 hours for email verification
        self.max_verification_attempts = 10
    
    def generate_verification_token(self, user_id: int, email: str) -> str:
        """Generate a secure email verification token"""
        # Create a random token
        random_token = secrets.token_urlsafe(32)
        
        # Add user ID, email, and timestamp for additional security
        timestamp = str(int(datetime.utcnow().timestamp()))
        token_data = f"{user_id}:{email}:{timestamp}:{random_token}"
        
        # Hash the token for storage
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        return f"{user_id}:{email}:{timestamp}:{random_token}:{token_hash}"
    
    def validate_verification_token(self, token: str) -> Optional[tuple[int, str]]:
        """Validate email verification token and return user ID and email if valid"""
        try:
            parts = token.split(":")
            if len(parts) != 5:
                return None
            
            user_id, email, timestamp, random_token, provided_hash = parts
            
            # Recreate the token data
            token_data = f"{user_id}:{email}:{timestamp}:{random_token}"
            expected_hash = hashlib.sha256(token_data.encode()).hexdigest()
            
            # Verify hash
            if provided_hash != expected_hash:
                logger.warning(f"Invalid verification token hash for user {user_id}")
                return None
            
            # Check expiry
            token_time = datetime.fromtimestamp(int(timestamp))
            expiry_time = token_time + timedelta(hours=self.token_expiry_hours)
            
            if datetime.utcnow() > expiry_time:
                logger.info(f"Expired verification token for user {user_id}")
                return None
            
            return int(user_id), email
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid verification token format: {e}")
            return None
    
    def send_verification_email(self, db: Session, user_id: int) -> bool:
        """Send email verification to user"""
        try:
            # Get user
            user = crud.get_user(db, user_id)
            if not user:
                logger.error(f"User not found for verification: {user_id}")
                return False
            
            # Check if already verified
            if user.email_verified:
                logger.info(f"Email already verified for user: {user_id}")
                return True
            
            # Generate verification token
            verification_token = self.generate_verification_token(user.id, user.email)
            
            # Store token in database
            verification_data = {
                "token": verification_token,
                "created_at": datetime.utcnow().isoformat(),
                "attempts": 0,
                "email": user.email
            }
            
            # Update user with verification token info
            user.email_verification_data = verification_data
            db.commit()
            
            # Send verification email
            send_verification_email(user.email, user.name, verification_token)
            
            logger.info(f"Verification email sent to user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to user {user_id}: {e}")
            db.rollback()
            return False
    
    def verify_email(self, db: Session, token: str) -> bool:
        """Verify user email using token"""
        try:
            # Validate token
            result = self.validate_verification_token(token)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification token"
                )
            
            user_id, email = result
            
            # Get user
            user = crud.get_user(db, user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification token"
                )
            
            # Check if email matches
            if user.email != email:
                logger.warning(f"Email mismatch in verification token for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification token"
                )
            
            # Check verification attempts
            verification_data = getattr(user, 'email_verification_data', {})
            attempts = verification_data.get('attempts', 0)
            
            if attempts >= self.max_verification_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many verification attempts. Please request a new verification email."
                )
            
            # Mark email as verified
            user.email_verified = True
            user.email_verified_at = datetime.utcnow()
            user.email_verification_data = None  # Clear verification data
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Email verified successfully for user ID: {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify email: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify email"
            )
    
    def resend_verification_email(self, db: Session, user_id: int) -> bool:
        """Resend verification email to user"""
        try:
            # Get user
            user = crud.get_user(db, user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if already verified
            if user.email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already verified"
                )
            
            # Check rate limiting for resend
            verification_data = getattr(user, 'email_verification_data', {})
            if verification_data and 'created_at' in verification_data:
                last_sent = datetime.fromisoformat(verification_data['created_at'])
                if datetime.utcnow() - last_sent < timedelta(minutes=5):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Please wait 5 minutes before requesting another verification email"
                    )
            
            # Send new verification email
            return self.send_verification_email(db, user_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to resend verification email to user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend verification email"
            )
    
    def cleanup_expired_tokens(self, db: Session):
        """Clean up expired email verification tokens"""
        try:
            expiry_time = datetime.utcnow() - timedelta(hours=self.token_expiry_hours)
            
            # Find users with expired verification tokens
            users_with_tokens = db.query(models.User).filter(
                models.User.email_verification_data.isnot(None),
                models.User.email_verified == False
            ).all()
            
            cleaned_count = 0
            for user in users_with_tokens:
                verification_data = user.email_verification_data
                if verification_data and 'created_at' in verification_data:
                    created_at = datetime.fromisoformat(verification_data['created_at'])
                    if created_at < expiry_time:
                        user.email_verification_data = None
                        cleaned_count += 1
            
            if cleaned_count > 0:
                db.commit()
                logger.info(f"Cleaned up {cleaned_count} expired email verification tokens")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired verification tokens: {e}")
            db.rollback()
    
    def is_email_verified(self, db: Session, user_id: int) -> bool:
        """Check if user's email is verified"""
        user = crud.get_user(db, user_id)
        return user.email_verified if user else False

# Global email verification manager instance
email_verification_manager = EmailVerificationManager()

# Convenience functions
def send_verification_email(db: Session, user_id: int) -> bool:
    """Send email verification to user"""
    return email_verification_manager.send_verification_email(db, user_id)

def verify_email(db: Session, token: str) -> bool:
    """Verify user email using token"""
    return email_verification_manager.verify_email(db, token)

def resend_verification_email(db: Session, user_id: int) -> bool:
    """Resend verification email to user"""
    return email_verification_manager.resend_verification_email(db, user_id)

def is_email_verified(db: Session, user_id: int) -> bool:
    """Check if user's email is verified"""
    return email_verification_manager.is_email_verified(db, user_id)

def cleanup_expired_verification_tokens(db: Session):
    """Clean up expired email verification tokens"""
    email_verification_manager.cleanup_expired_tokens(db)
