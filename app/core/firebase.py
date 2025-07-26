import firebase_admin
from firebase_admin import credentials,auth
from fastapi import HTTPException, status
from typing import Optional
from app.config import settings

def initialize_firebase():
    try:
        # Check if Firebase app is already initialized
        try:
            firebase_admin.get_app()
            print("Firebase app already initialized")
            return
        except ValueError:
            # App not initialized, proceed with initialization
            pass

        print(f"Initializing Firebase with credentials: {settings.FIREBASE_CREDENTIALS}")
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")

    except FileNotFoundError:
        print(f"Firebase credentials file not found: {settings.FIREBASE_CREDENTIALS}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase credentials file not found: {settings.FIREBASE_CREDENTIALS}"
        )
    except Exception as e:
        print(f"Firebase initialization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase initialization failed: {str(e)}"
        )
    

async def verify_token(id_token: str) -> dict:
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Error verifying Firebase ID token: {str(e)}',
            headers={"WWW-Authenticate": "Bearer"},
        )
    
async def get_firebase_user(uid: str):
    try:
        return auth.get_user(uid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching Firebase user: {str(e)}"
        )

async def create_firebase_user(email: str, name: str, password: str, phone: Optional[str] = None) -> dict:
    """
    Create a new user in Firebase Authentication
    """
    try:
        user_data = {
            'email': email,
            'password': password,
            'email_verified': False,
            'display_name': name,
            'disabled': False,
        }

        # Add phone number if provided
        if phone:
            user_data['phone_number'] = phone if phone.startswith('+') else f'+91{phone}'

        # Create user in Firebase
        firebase_user = auth.create_user(**user_data)

        return {
            'uid': firebase_user.uid,
            'email': firebase_user.email,
            'display_name': firebase_user.display_name,
            'phone_number': getattr(firebase_user, 'phone_number', None),
            'email_verified': firebase_user.email_verified,
            'disabled': firebase_user.disabled,
            'creation_time': getattr(firebase_user.user_metadata, 'creation_time', None),
            'last_sign_in_time': getattr(firebase_user.user_metadata, 'last_sign_in_time', None)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating Firebase user: {str(e)}"
        )

async def update_firebase_user(uid: str, **kwargs) -> dict:
    """
    Update an existing Firebase user
    """
    try:
        firebase_user = auth.update_user(uid, **kwargs)
        return {
            'uid': firebase_user.uid,
            'email': firebase_user.email,
            'display_name': firebase_user.display_name,
            'phone_number': getattr(firebase_user, 'phone_number', None),
            'email_verified': firebase_user.email_verified,
            'disabled': firebase_user.disabled
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating Firebase user: {str(e)}"
        )

async def delete_firebase_user(uid: str) -> bool:
    """
    Delete a Firebase user
    """
    try:
        auth.delete_user(uid)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting Firebase user: {str(e)}"
        )

async def set_firebase_custom_claims(uid: str, custom_claims: dict) -> bool:
    """
    Set custom claims for a Firebase user (for role-based access)
    """
    try:
        auth.set_custom_user_claims(uid, custom_claims)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error setting custom claims: {str(e)}"
        )