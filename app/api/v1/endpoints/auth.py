from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core import security
from app.core.firebase import verify_token, get_firebase_user, create_firebase_user, set_firebase_custom_claims, delete_firebase_user
from app.core.ai_services import ai_service
from app.db.session import get_db
from app.db import crud
from app.schemas.users import UserInDB, UserRegistration, UserRegistrationResponse
from app.utils.notifications import create_notification
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/test-register")
async def test_register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """
    Simple test registration endpoint for debugging
    """
    try:
        # Check if user already exists
        existing_user = crud.get_user_by_email(db, user_data.email)
        if existing_user:
            return {"error": "User already exists"}

        # Prepare user data
        user_dict = user_data.model_dump()
        user_dict.pop('preferences', {})
        user_dict.pop('location', None)

        # Add firebase_uid
        import uuid
        user_dict['firebase_uid'] = f"temp_{uuid.uuid4().hex[:20]}"

        # Create user
        db_user = crud.create_user(db, user_dict)

        return {
            "success": True,
            "user_id": db_user.id,
            "email": db_user.email
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

class LoginRequest(BaseModel):
    id_token: str

@router.post("/login")
async def login_with_firebase(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Login attempt with token: {login_data.id_token[:20]}...")

        # Verify the Firebase ID token
        decoded_token = await verify_token(login_data.id_token)
        firebase_uid = decoded_token["uid"]

        logger.info(f"Token verified for Firebase UID: {firebase_uid}")

        # Get user from database
        db_user = crud.get_user_by_firebase_uid(db, firebase_uid)

        if not db_user:
            logger.info(f"User not found in database, creating from Firebase data")

            # Get user data from Firebase
            firebase_user = await get_firebase_user(firebase_uid)

            # Handle phone number properly - use None instead of empty string to avoid unique constraint issues
            phone_number = firebase_user.phone_number
            if phone_number and phone_number.strip():
                # Clean phone number (remove country code if present)
                phone_number = phone_number.replace('+91', '').replace('+', '').strip()
            else:
                phone_number = None

            user_data = {
                "firebase_uid": firebase_uid,
                "email": firebase_user.email,
                "name": firebase_user.display_name or "User",
                "phone": phone_number,
                "role": "tenant",
                "is_active": True,
                "kyc_verified": False
            }

            logger.info(f"Creating database user with data: {user_data}")

            try:
                db_user = crud.create_user(db, user_data)
                logger.info(f"Database user created with ID: {db_user.id}")
            except Exception as e:
                logger.error(f"Failed to create user in database: {str(e)}")
                # If it's a unique constraint violation, try to find existing user by email
                if "unique constraint" in str(e).lower():
                    existing_user = crud.get_user_by_email(db, firebase_user.email)
                    if existing_user:
                        logger.info(f"Found existing user by email: {existing_user.id}")
                        # Update the existing user with Firebase UID
                        existing_user.firebase_uid = firebase_uid
                        db.commit()
                        db.refresh(existing_user)
                        db_user = existing_user
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to create user account"
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user account"
                    )

        logger.info(f"Login successful for user: {db_user.email}")

        return {
            "access_token": login_data.id_token,
            "token_type": "bearer",
            "user": UserInDB.model_validate(db_user)
        }

    except HTTPException as e:
        logger.error(f"HTTP Exception during login: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user information"""
    try:
        # Get authorization header from request
        authorization = request.headers.get("authorization")

        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )

        token = authorization.replace("Bearer ", "")
        decoded_token = await verify_token(token)
        firebase_uid = decoded_token["uid"]

        # Get user from database
        db_user = crud.get_user_by_firebase_uid(db, firebase_uid)

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "user": UserInDB.model_validate(db_user),
            "firebase_uid": firebase_uid,
            "token_valid": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )

@router.post("/register", response_model=UserRegistrationResponse)
async def register_user(
    user_data: UserRegistration,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user with AI-powered fraud detection and personalized recommendations
    """
    try:
        logger.info(f"Starting registration for email: {user_data.email}")

        # Check if user already exists
        existing_user = crud.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Prepare user data
        user_dict = user_data.model_dump()
        preferences = user_dict.pop('preferences', {})
        location = user_dict.pop('location', None)
        password = user_dict.pop('password')  # Remove password from user_dict (don't store in DB)

        logger.info(f"Creating Firebase user for email: {user_data.email}")

        # Step 1: Create user in Firebase Authentication
        try:
            # Clean phone number if provided
            phone_for_firebase = None
            if user_data.phone and user_data.phone.strip():
                phone_for_firebase = user_data.phone.strip()

            firebase_user = await create_firebase_user(
                email=user_data.email,
                name=user_data.name,
                password=password,
                phone=phone_for_firebase
            )
            logger.info(f"Firebase user created with UID: {firebase_user['uid']}")

            # Set custom claims for role-based access
            await set_firebase_custom_claims(firebase_user['uid'], {
                'role': user_data.role,
                'email_verified': False,
                'kyc_verified': False
            })

        except HTTPException as e:
            logger.error(f"Failed to create Firebase user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create Firebase user: {e.detail}"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating Firebase user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account in authentication system"
            )

        # Step 2: Create user in local database with Firebase UID
        # Prepare database user data (only include fields that exist in the User model)
        # Handle phone number properly - use None instead of empty string
        phone_for_db = None
        if user_data.phone and user_data.phone.strip():
            phone_for_db = user_data.phone.strip()

        db_user_data = {
            'firebase_uid': firebase_user['uid'],
            'email': user_data.email,
            'phone': phone_for_db,
            'name': user_data.name,
            'role': user_data.role,
            'is_active': True,
            'kyc_verified': False
        }

        logger.info(f"Creating database user with data: {db_user_data}")

        try:
            # Check if user already exists by email or phone
            existing_user_email = crud.get_user_by_email(db, user_data.email)
            if existing_user_email:
                # Clean up Firebase user since we can't create database user
                try:
                    await delete_firebase_user(firebase_user['uid'])
                except:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )

            # Check phone number only if provided
            if user_data.phone and user_data.phone.strip():
                existing_user_phone = crud.get_user_by_phone(db, user_data.phone.strip())
                if existing_user_phone:
                    # Clean up Firebase user since we can't create database user
                    try:
                        await delete_firebase_user(firebase_user['uid'])
                    except:
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User with this phone number already exists"
                    )

            db_user = crud.create_user(db, db_user_data)
            logger.info(f"Database user created successfully with ID: {db_user.id}")
        except HTTPException:
            # Re-raise HTTP exceptions (like duplicate user)
            raise
        except Exception as e:
            logger.error(f"Failed to create database user: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"User data: {db_user_data}")

            # If database creation fails, we should clean up the Firebase user
            try:
                await delete_firebase_user(firebase_user['uid'])
                logger.info(f"Cleaned up Firebase user: {firebase_user['uid']}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup Firebase user: {str(cleanup_error)}")

            # Provide more specific error message
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg:
                if "email" in error_msg:
                    detail = "User with this email already exists"
                elif "phone" in error_msg:
                    detail = "User with this phone number already exists"
                elif "firebase_uid" in error_msg:
                    detail = "Firebase user already exists"
                else:
                    detail = "User with this information already exists"
            else:
                detail = f"Failed to create user account in database: {error_msg}"

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail
            )

        # AI-powered fraud detection
        logger.info("Running fraud detection...")
        fraud_analysis = await ai_service.detect_fraud(
            property_data={},
            user_data={
                "email": user_data.email,
                "phone": user_data.phone,
                "name": user_data.name,
                "location": location,
                "properties_posted": 0,
                "kyc_verified": False
            }
        )
        logger.info(f"Fraud analysis completed: {fraud_analysis}")

        # Skip recommendations for now to isolate the issue
        recommendations = []

        # Create welcome notification
        logger.info("Creating welcome notification...")
        try:
            await create_notification(
                db=db,
                user_id=getattr(db_user, 'id'),
                title="Welcome to DreamBig!",
                message="Your account has been created successfully. Start exploring properties now!",
                notification_type="welcome"
            )
            logger.info("Welcome notification created successfully")
        except Exception as e:
            logger.warning(f"Failed to create welcome notification: {str(e)}")

        logger.info("Preparing response...")
        response = UserRegistrationResponse(
            user=UserInDB.model_validate(db_user),
            recommendations=recommendations,
            fraud_score=fraud_analysis
        )

        logger.info(f"Registration completed successfully - DB ID: {db_user.id}, Firebase UID: {firebase_user['uid']}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/verify-firebase/{user_id}")
async def verify_firebase_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Verify that a database user exists in Firebase Authentication
    """
    try:
        # Get user from database
        db_user = crud.get_user(db, user_id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )

        # Get user from Firebase
        firebase_user = await get_firebase_user(str(db_user.firebase_uid))

        return {
            "database_user": {
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.name,
                "firebase_uid": db_user.firebase_uid,
                "role": db_user.role,
                "created_at": db_user.created_at
            },
            "firebase_user": {
                "uid": firebase_user.uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name,
                "email_verified": firebase_user.email_verified,
                "disabled": firebase_user.disabled,
                "phone_number": getattr(firebase_user, 'phone_number', None)
            },
            "sync_status": "synchronized" if db_user.email == firebase_user.email else "out_of_sync"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying Firebase user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

@router.get("/users-firebase-status")
async def get_users_firebase_status(
    db: Session = Depends(get_db)
):
    """
    Get all users and their Firebase synchronization status
    """
    try:
        # Get all users from database
        users = crud.get_users(db, skip=0, limit=100)

        user_status = []
        for user in users:
            user_info = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "firebase_uid": user.firebase_uid,
                "role": user.role,
                "created_at": str(user.created_at),
                "firebase_status": "unknown"
            }

            # Check if user exists in Firebase
            try:
                firebase_user = await get_firebase_user(str(user.firebase_uid))
                user_info["firebase_status"] = "exists"
                user_info["firebase_email"] = firebase_user.email
                user_info["firebase_verified"] = firebase_user.email_verified
            except Exception:
                user_info["firebase_status"] = "not_found"

            user_status.append(user_info)

        return {
            "total_users": len(user_status),
            "users": user_status
        }

    except Exception as e:
        logger.error(f"Error getting users Firebase status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users status: {str(e)}"
        )

@router.post("/create-test-token/{user_id}")
async def create_test_token(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Create a custom Firebase token for testing purposes
    IMPORTANT: This should only be used for development/testing!
    """
    try:
        # Get user from database
        db_user = crud.get_user(db, user_id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Create custom token
        from firebase_admin import auth
        custom_token = auth.create_custom_token(
            str(db_user.firebase_uid),
            {
                'role': str(db_user.role),
                'email': str(db_user.email),
                'name': str(db_user.name),
                'user_id': getattr(db_user, 'id')
            }
        )

        return {
            "user_id": getattr(db_user, 'id'),
            "firebase_uid": str(db_user.firebase_uid),
            "email": str(db_user.email),
            "custom_token": custom_token.decode('utf-8'),
            "instructions": {
                "step_1": "Use this custom token to sign in to Firebase on the client side",
                "step_2": "After signing in, call user.getIdToken() to get the ID token",
                "step_3": "Use the ID token in Authorization header: 'Bearer <id_token>'",
                "warning": "This endpoint is for testing only - remove in production!"
            }
        }

    except Exception as e:
        logger.error(f"Error creating test token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test token: {str(e)}"
        )

@router.post("/kyc", dependencies=[Depends(security.get_current_active_user)])
async def submit_kyc(
    kyc_details: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.get_current_active_user)
):
    """
    Submit KYC details with AI-powered fraud detection
    """
    try:
        # AI-powered fraud detection for KYC
        fraud_analysis = await ai_service.detect_fraud(
            property_data={},
            user_data={
                "email": getattr(current_user, 'email', ''),
                "phone": getattr(current_user, 'phone', ''),
                "name": getattr(current_user, 'name', ''),
                "kyc_details": kyc_details,
                "properties_posted": len(crud.get_properties_by_owners(db, getattr(current_user, 'id'), "available")),
                "kyc_verified": False
            }
        )

        # If fraud score is too high, reject KYC
        if fraud_analysis.get("is_fraud", False) and fraud_analysis.get("confidence", 0) > 0.7:
            await create_notification(
                db=db,
                user_id=getattr(current_user, 'id'),
                title="KYC Verification Failed",
                message="Your KYC submission requires manual review due to security concerns.",
                notification_type="kyc_failed"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KYC verification failed. Please contact support."
            )

        # Update user KYC
        updated_user = crud.update_user_kyc(db, user_id=getattr(current_user, 'id'), kyc_details=kyc_details)

        # Create success notification
        await create_notification(
            db=db,
            user_id=getattr(current_user, 'id'),
            title="KYC Verified Successfully",
            message="Your identity has been verified. You can now access all features.",
            notification_type="kyc_success"
        )

        return {
            "user": UserInDB.model_validate(updated_user),
            "fraud_analysis": fraud_analysis,
            "message": "KYC submitted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during KYC submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KYC submission failed. Please try again."
        )


# Admin endpoints
@router.get("/admin/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.get_current_admin_user)
):
    """
    Get all users (admin only)
    """
    try:
        users = crud.get_users(db, skip=skip, limit=limit)
        return [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                "kyc_verified": user.kyc_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/admin/users/{user_id}")
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.get_current_admin_user)
):
    """
    Get user by ID (admin only)
    """
    try:
        user = crud.get_user(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "kyc_verified": user.kyc_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "firebase_uid": user.firebase_uid
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )
