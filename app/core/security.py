from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.firebase import verify_token
from app.db.crud import get_user_by_firebase_uid
from app.db.session import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import JWTError, jwt
from app.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        # First try JWT token (for testing)
        try:
            payload = decode_access_token(credentials.credentials)
            user_id = payload.get("sub")
            if user_id:
                from app.db import crud
                user = crud.get_user(db, user_id=int(user_id))
                if user:
                    return user
        except:
            pass  # If JWT fails, try Firebase

        # Try Firebase token
        decode_token = await verify_token(credentials.credentials)
        firebase_uid = decode_token['uid']
        user = get_user_by_firebase_uid(db, firebase_uid)
        if not user:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="User Not Found in database"
            )
        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
def get_current_active_user(current_user = Depends(get_current_user)):
    if hasattr(current_user, 'is_active'):
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user = Depends(get_current_active_user)):
    print(f"DEBUG: Admin check - user: {current_user}")
    print(f"DEBUG: Admin check - has role attr: {hasattr(current_user, 'role')}")

    if hasattr(current_user, 'role'):
        print(f"DEBUG: Admin check - role: {current_user.role}")
        print(f"DEBUG: Admin check - role type: {type(current_user.role)}")

        # Handle enum case (UserRole.ADMIN)
        role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        print(f"DEBUG: Admin check - role value: {role_value}")

        if role_value != "admin":
            print(f"DEBUG: Admin check - FAILED: {role_value} != 'admin'")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
        else:
            print(f"DEBUG: Admin check - PASSED")
    else:
        # Handle dict case
        role = current_user.get('role') if current_user else None
        print(f"DEBUG: Admin check - dict role: {role}")
        if role != "admin":
            print(f"DEBUG: Admin check - FAILED: dict {role} != 'admin'")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
        else:
            print(f"DEBUG: Admin check - PASSED (dict)")

    return current_user


# JWT Token functions for testing purposes
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token for testing purposes."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode JWT access token for testing purposes."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_firebase_token(token: str):
    """Verify Firebase token - wrapper for compatibility."""
    import asyncio
    return asyncio.run(verify_token(token))
