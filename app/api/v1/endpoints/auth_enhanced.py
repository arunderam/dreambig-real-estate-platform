"""
Enhanced authentication endpoints with security features
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.password_reset import initiate_password_reset, reset_password, change_password
from app.core.email_verification import send_verification_email, verify_email, resend_verification_email
from app.core.rate_limiting import auth_rate_limit, user_rate_limit
from app.core.csrf_protection import generate_csrf_token, set_csrf_cookie
from app.utils.email import send_welcome_email

router = APIRouter()

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class EmailVerificationRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

@router.post("/login", response_model=schemas.Token)
@auth_rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
async def login_for_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your email for verification link."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    # Generate CSRF token
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "csrf_token": csrf_token
    }

@router.post("/register", response_model=schemas.User)
@auth_rate_limit(limit=3, window=300)  # 3 registrations per 5 minutes
async def register(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user with email verification
    """
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    
    # Create user (email_verified will be False by default)
    user = crud.create_user(db, obj_in=user_in)
    
    # Send welcome email
    send_welcome_email(user.email, user.name)
    
    # Send verification email
    send_verification_email(db, user.id)
    
    return user

@router.post("/password-reset/request")
@auth_rate_limit(limit=3, window=300)  # 3 requests per 5 minutes
async def request_password_reset(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    password_reset: PasswordResetRequest
) -> Any:
    """
    Request password reset email
    """
    # Always return success to prevent email enumeration
    initiate_password_reset(db, password_reset.email)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/password-reset/confirm")
@auth_rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
async def confirm_password_reset(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    password_reset: PasswordResetConfirm
) -> Any:
    """
    Confirm password reset with token
    """
    reset_password(db, password_reset.token, password_reset.new_password)
    
    return {"message": "Password has been reset successfully"}

@router.post("/password-change")
@user_rate_limit(limit=5, window=300)  # 5 changes per 5 minutes
async def change_user_password(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    password_change: PasswordChange,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Change user password (requires current password)
    """
    change_password(
        db, 
        current_user.id, 
        password_change.current_password, 
        password_change.new_password
    )
    
    return {"message": "Password changed successfully"}

@router.post("/email-verification/verify")
@auth_rate_limit(limit=10, window=300)  # 10 attempts per 5 minutes
async def verify_user_email(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    verification: EmailVerificationRequest
) -> Any:
    """
    Verify user email with token
    """
    verify_email(db, verification.token)
    
    return {"message": "Email verified successfully"}

@router.post("/email-verification/resend")
@auth_rate_limit(limit=3, window=300)  # 3 resends per 5 minutes
async def resend_verification_email_endpoint(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    resend_request: ResendVerificationRequest
) -> Any:
    """
    Resend email verification
    """
    # Find user by email
    user = crud.get_user_by_email(db, resend_request.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists and is not verified, a verification email has been sent"}
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    resend_verification_email(db, user.id)
    
    return {"message": "Verification email sent"}

@router.get("/me", response_model=schemas.User)
@user_rate_limit(limit=100, window=60)  # 100 requests per minute
async def read_users_me(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user
    """
    return current_user

@router.put("/me", response_model=schemas.User)
@user_rate_limit(limit=10, window=300)  # 10 updates per 5 minutes
async def update_user_me(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user
    """
    # If email is being changed, require re-verification
    if user_in.email and user_in.email != current_user.email:
        user_in_dict = user_in.dict(exclude_unset=True)
        user_in_dict["email_verified"] = False
        user_in = schemas.UserUpdate(**user_in_dict)
    
    user = crud.update_user(db, db_obj=current_user, obj_in=user_in)
    
    # If email was changed, send new verification email
    if user_in.email and user_in.email != current_user.email:
        send_verification_email(db, user.id)
    
    return user

@router.post("/logout")
@user_rate_limit(limit=20, window=60)  # 20 logouts per minute
async def logout(
    request: Request,
    response: Response,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Logout user (clear cookies)
    """
    # Clear CSRF cookie
    response.delete_cookie("csrf_token")
    
    # In a more sophisticated implementation, you might:
    # 1. Blacklist the current token
    # 2. Clear session data
    # 3. Log the logout event
    
    return {"message": "Logged out successfully"}

@router.get("/csrf-token")
async def get_csrf_token(response: Response) -> Any:
    """
    Get CSRF token for forms
    """
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)
    
    return {"csrf_token": csrf_token}
