"""
Password reset functionality
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.db import crud, models
from app.core.security import verify_password, get_password_hash
from app.utils.email import send_password_reset_email
from app.utils.validation import validate_password

logger = logging.getLogger(__name__)

class PasswordResetManager:
    """Manages password reset tokens and operations"""
    
    def __init__(self):
        self.token_expiry_hours = 24
        self.max_reset_attempts = 5
    
    def generate_reset_token(self, user_id: int) -> str:
        """Generate a secure password reset token"""
        # Create a random token
        random_token = secrets.token_urlsafe(32)
        
        # Add user ID and timestamp for additional security
        timestamp = str(int(datetime.utcnow().timestamp()))
        token_data = f"{user_id}:{timestamp}:{random_token}"
        
        # Hash the token for storage
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        return f"{user_id}:{timestamp}:{random_token}:{token_hash}"
    
    def validate_reset_token(self, token: str) -> Optional[int]:
        """Validate password reset token and return user ID if valid"""
        try:
            parts = token.split(":")
            if len(parts) != 4:
                return None
            
            user_id, timestamp, random_token, provided_hash = parts
            
            # Recreate the token data
            token_data = f"{user_id}:{timestamp}:{random_token}"
            expected_hash = hashlib.sha256(token_data.encode()).hexdigest()
            
            # Verify hash
            if provided_hash != expected_hash:
                logger.warning(f"Invalid token hash for user {user_id}")
                return None
            
            # Check expiry
            token_time = datetime.fromtimestamp(int(timestamp))
            expiry_time = token_time + timedelta(hours=self.token_expiry_hours)
            
            if datetime.utcnow() > expiry_time:
                logger.info(f"Expired token for user {user_id}")
                return None
            
            return int(user_id)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid token format: {e}")
            return None
    
    def initiate_password_reset(self, db: Session, email: str) -> bool:
        """Initiate password reset process"""
        try:
            # Find user by email
            user = crud.get_user_by_email(db, email)
            if not user:
                # Don't reveal if email exists or not
                logger.info(f"Password reset requested for non-existent email: {email}")
                return True
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Password reset requested for inactive user: {email}")
                return True
            
            # Generate reset token
            reset_token = self.generate_reset_token(user.id)
            
            # Store token in database (you might want to create a separate table for this)
            # For now, we'll store it in user's record with expiry
            reset_data = {
                "token": reset_token,
                "created_at": datetime.utcnow(),
                "attempts": 0
            }
            
            # Update user with reset token info
            user.password_reset_data = reset_data
            db.commit()
            
            # Send reset email
            send_password_reset_email(user.email, user.name, reset_token)
            
            logger.info(f"Password reset initiated for user: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initiate password reset for {email}: {e}")
            db.rollback()
            return False
    
    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """Reset user password using token"""
        try:
            # Validate token
            user_id = self.validate_reset_token(token)
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # Get user
            user = crud.get_user(db, user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            # Check reset attempts
            reset_data = getattr(user, 'password_reset_data', {})
            attempts = reset_data.get('attempts', 0)
            
            if attempts >= self.max_reset_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many reset attempts. Please request a new reset link."
                )
            
            # Validate new password
            validate_password(new_password)
            
            # Hash new password
            hashed_password = get_password_hash(new_password)
            
            # Update user password
            user.hashed_password = hashed_password
            user.password_reset_data = None  # Clear reset data
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Password reset successful for user ID: {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to reset password: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
    
    def change_password(
        self, 
        db: Session, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password (requires current password)"""
        try:
            # Get user
            user = crud.get_user(db, user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Validate new password
            validate_password(new_password)
            
            # Check if new password is different from current
            if verify_password(new_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password must be different from current password"
                )
            
            # Hash new password
            hashed_password = get_password_hash(new_password)
            
            # Update user password
            user.hashed_password = hashed_password
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Password changed successfully for user ID: {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    
    def cleanup_expired_tokens(self, db: Session):
        """Clean up expired password reset tokens"""
        try:
            # This would be better implemented with a separate tokens table
            # For now, we'll clean up tokens stored in user records
            
            expiry_time = datetime.utcnow() - timedelta(hours=self.token_expiry_hours)
            
            # Find users with expired reset tokens
            users_with_tokens = db.query(models.User).filter(
                models.User.password_reset_data.isnot(None)
            ).all()
            
            cleaned_count = 0
            for user in users_with_tokens:
                reset_data = user.password_reset_data
                if reset_data and 'created_at' in reset_data:
                    created_at = datetime.fromisoformat(reset_data['created_at'])
                    if created_at < expiry_time:
                        user.password_reset_data = None
                        cleaned_count += 1
            
            if cleaned_count > 0:
                db.commit()
                logger.info(f"Cleaned up {cleaned_count} expired password reset tokens")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            db.rollback()

# Global password reset manager instance
password_reset_manager = PasswordResetManager()

# Convenience functions
def initiate_password_reset(db: Session, email: str) -> bool:
    """Initiate password reset process"""
    return password_reset_manager.initiate_password_reset(db, email)

def reset_password(db: Session, token: str, new_password: str) -> bool:
    """Reset user password using token"""
    return password_reset_manager.reset_password(db, token, new_password)

def change_password(
    db: Session, 
    user_id: int, 
    current_password: str, 
    new_password: str
) -> bool:
    """Change user password"""
    return password_reset_manager.change_password(
        db, user_id, current_password, new_password
    )

def cleanup_expired_tokens(db: Session):
    """Clean up expired password reset tokens"""
    password_reset_manager.cleanup_expired_tokens(db)
