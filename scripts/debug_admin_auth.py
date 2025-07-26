#!/usr/bin/env python3
"""
Debug Admin Authentication Issue
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quick_token import generate_quick_token
from app.core.security import decode_access_token
from app.db.session import SessionLocal, engine
from app.db.models import Base
from app.db import crud

def debug_admin_auth():
    """Debug admin authentication issue."""
    
    # Create database session
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Generate admin token
        print("🔍 Generating admin token...")
        result = generate_quick_token("admin")
        token = result["access_token"]
        user_info = result["user"]
        
        print(f"✅ Generated token for user: {user_info}")
        
        # Decode the token
        print("\n🔍 Decoding JWT token...")
        payload = decode_access_token(token)
        print(f"✅ Token payload: {payload}")
        
        # Get user from database
        print("\n🔍 Getting user from database...")
        user_id = payload.get("sub")
        user = crud.get_user(db, user_id=int(user_id))
        
        if user:
            print(f"✅ Found user in database:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.name}")
            print(f"   Role: {user.role}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Has role attribute: {hasattr(user, 'role')}")
            print(f"   Role type: {type(user.role)}")
            print(f"   Role == 'admin': {user.role == 'admin'}")
        else:
            print("❌ User not found in database!")
        
        # Test the authentication flow manually
        print("\n🔍 Testing authentication flow...")
        
        # Simulate get_current_user
        print("Step 1: get_current_user would return:", user)
        
        # Simulate get_current_active_user
        if user and hasattr(user, 'is_active') and user.is_active:
            print("Step 2: get_current_active_user would pass")
        else:
            print("Step 2: get_current_active_user would fail")
        
        # Simulate get_current_admin_user
        if user and hasattr(user, 'role') and user.role == "admin":
            print("Step 3: get_current_admin_user would pass ✅")
        else:
            print("Step 3: get_current_admin_user would fail ❌")
            print(f"   Has role: {hasattr(user, 'role') if user else 'No user'}")
            print(f"   Role value: {user.role if user else 'No user'}")
            print(f"   Role == 'admin': {user.role == 'admin' if user else 'No user'}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    debug_admin_auth()
