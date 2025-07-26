#!/usr/bin/env python3
"""
Quick Token Generator for API Testing

Simple script to quickly generate authentication tokens for common test scenarios.

Usage:
    python scripts/quick_token.py                    # Default tenant user
    python scripts/quick_token.py admin              # Admin user
    python scripts/quick_token.py owner              # Property owner
    python scripts/quick_token.py custom email@test.com "Test User"
"""

import sys
import json
from pathlib import Path
from datetime import timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import create_access_token
from app.config import settings
from app.db import crud
from app.db.models import Base

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Predefined test users
TEST_USERS = {
    "tenant": {
        "email": "tenant@dreambig.com",
        "name": "Test Tenant",
        "role": "tenant",
        "phone": "+1234567890"
    },
    "owner": {
        "email": "owner@dreambig.com", 
        "name": "Test Property Owner",
        "role": "owner",
        "phone": "+1234567891"
    },
    "admin": {
        "email": "admin@dreambig.com",
        "name": "Test Admin",
        "role": "admin", 
        "phone": "+1234567892"
    }
}


def get_or_create_user(db: Session, user_type: str = "tenant", email: str = None, name: str = None):
    """Get or create a test user."""
    if user_type in TEST_USERS:
        user_data = TEST_USERS[user_type].copy()
    else:
        # Custom user
        user_data = {
            "email": email or "custom@dreambig.com",
            "name": name or "Custom User",
            "role": "tenant",
            "phone": "+1234567899"
        }
    
    # Try to find existing user
    user = crud.get_user_by_email(db, user_data["email"])
    
    if not user:
        # Create new user
        user_data["firebase_uid"] = f"test_uid_{user_data['email'].replace('@', '_').replace('.', '_')}"
        user_data["kyc_verified"] = True
        
        user = crud.create_user(db, user_data)
        print(f"✅ Created user: {user.name} ({user.email})")
    else:
        print(f"🔍 Found existing user: {user.name} ({user.email})")
    
    return user


def generate_quick_token(user_type: str = "tenant", email: str = None, name: str = None):
    """Generate a quick authentication token."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get or create user
        user = get_or_create_user(db, user_type, email, name)
        
        # Generate token
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "firebase_uid": user.firebase_uid
        }
        
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(data=token_data, expires_delta=expires_delta)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }
    
    finally:
        db.close()


def main():
    """Main function."""
    if len(sys.argv) == 1:
        # Default: tenant user
        user_type = "tenant"
        email = None
        name = None
    elif len(sys.argv) == 2:
        # User type specified
        user_type = sys.argv[1].lower()
        email = None
        name = None
    elif len(sys.argv) == 4 and sys.argv[1].lower() == "custom":
        # Custom user: python quick_token.py custom email@test.com "Test User"
        user_type = "custom"
        email = sys.argv[2]
        name = sys.argv[3]
    else:
        print("Usage:")
        print("  python scripts/quick_token.py                    # Default tenant user")
        print("  python scripts/quick_token.py admin              # Admin user")
        print("  python scripts/quick_token.py owner              # Property owner")
        print("  python scripts/quick_token.py custom email@test.com \"Test User\"")
        sys.exit(1)
    
    try:
        # Generate token
        result = generate_quick_token(user_type, email, name)
        
        # Output
        print(f"\n🎫 Quick Token Generated:")
        print("=" * 50)
        print(json.dumps(result, indent=2))
        print("=" * 50)
        
        # Quick copy-paste formats
        token = result["access_token"]
        print(f"\n📋 Quick Copy-Paste:")
        print(f"Authorization: Bearer {token}")
        print(f"\n🔗 Test Commands:")
        print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/v1/auth/me")
        print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/v1/properties/")
        
        # Save to temp file for easy access
        temp_file = project_root / "temp_token.txt"
        with open(temp_file, 'w') as f:
            f.write(token)
        print(f"\n💾 Token saved to: {temp_file}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
