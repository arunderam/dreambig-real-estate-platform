#!/usr/bin/env python3
"""
Authentication Token Generator for DreamBig Real Estate Platform API Testing

This script generates JWT tokens for testing API endpoints without going through
the full Firebase authentication flow.

Usage:
    python scripts/generate_auth_token.py --email user@example.com
    python scripts/generate_auth_token.py --user-id 1 --role admin
    python scripts/generate_auth_token.py --create-user --email test@example.com --name "Test User"
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.config import settings
from app.db.database import SessionLocal, engine
from app.db import crud
from app.db.models import Base


def get_db_session():
    """Get database session."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def find_user_by_email(db: Session, email: str):
    """Find user by email."""
    return crud.get_user_by_email(db, email)


def find_user_by_id(db: Session, user_id: int):
    """Find user by ID."""
    return crud.get_user(db, user_id)


def create_test_user(db: Session, email: str, name: str, role: str = "tenant", phone: str = None):
    """Create a test user."""
    user_data = {
        "email": email,
        "name": name,
        "role": role,
        "firebase_uid": f"test_uid_{email.replace('@', '_').replace('.', '_')}",
        "phone": phone or f"+1234567890",
        "is_verified": True,
        "preferences": {
            "budget_min": 1000000,
            "budget_max": 5000000,
            "preferred_locations": ["Mumbai", "Delhi"]
        }
    }
    
    return crud.create_user(db, user_data)


def generate_token_for_user(user, expires_delta: timedelta = None):
    """Generate JWT token for user."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "firebase_uid": user.firebase_uid
    }
    
    return create_access_token(data=token_data, expires_delta=expires_delta)


def format_token_output(user, token, format_type="json"):
    """Format token output."""
    user_info = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "firebase_uid": user.firebase_uid,
        "is_verified": user.is_verified
    }
    
    token_info = {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "user": user_info
    }
    
    if format_type == "json":
        return json.dumps(token_info, indent=2, default=str)
    elif format_type == "curl":
        return f'Authorization: Bearer {token}'
    elif format_type == "header":
        return f'"Authorization": "Bearer {token}"'
    elif format_type == "token":
        return token
    else:
        return token_info


def list_users(db: Session, limit: int = 10):
    """List existing users."""
    users = crud.get_users(db, skip=0, limit=limit)
    
    print(f"\n📋 Existing Users (showing {len(users)} users):")
    print("-" * 80)
    print(f"{'ID':<4} {'Email':<30} {'Name':<20} {'Role':<10} {'Verified':<8}")
    print("-" * 80)
    
    for user in users:
        print(f"{user.id:<4} {user.email:<30} {user.name:<20} {user.role:<10} {user.is_verified}")
    
    print("-" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Generate authentication tokens for API testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate token for existing user by email
  python scripts/generate_auth_token.py --email user@example.com
  
  # Generate token for existing user by ID
  python scripts/generate_auth_token.py --user-id 1
  
  # Create new user and generate token
  python scripts/generate_auth_token.py --create-user --email test@example.com --name "Test User"
  
  # Create admin user
  python scripts/generate_auth_token.py --create-user --email admin@example.com --name "Admin User" --role admin
  
  # Generate token with custom expiration (in minutes)
  python scripts/generate_auth_token.py --email user@example.com --expires 120
  
  # Output in different formats
  python scripts/generate_auth_token.py --email user@example.com --format curl
  python scripts/generate_auth_token.py --email user@example.com --format header
  python scripts/generate_auth_token.py --email user@example.com --format token
  
  # List existing users
  python scripts/generate_auth_token.py --list-users
        """
    )
    
    # User selection options
    user_group = parser.add_mutually_exclusive_group()
    user_group.add_argument("--email", help="Email of existing user")
    user_group.add_argument("--user-id", type=int, help="ID of existing user")
    user_group.add_argument("--create-user", action="store_true", help="Create new user")
    user_group.add_argument("--list-users", action="store_true", help="List existing users")
    
    # User creation options
    parser.add_argument("--name", help="Name for new user (required with --create-user)")
    parser.add_argument("--role", choices=["tenant", "owner", "admin"], default="tenant",
                       help="Role for new user (default: tenant)")
    parser.add_argument("--phone", help="Phone number for new user")
    
    # Token options
    parser.add_argument("--expires", type=int, help="Token expiration in minutes (default: from settings)")
    parser.add_argument("--format", choices=["json", "curl", "header", "token"], default="json",
                       help="Output format (default: json)")
    
    # Other options
    parser.add_argument("--save", help="Save token to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.create_user and not args.email:
        parser.error("--create-user requires --email")
    
    if args.create_user and not args.name:
        parser.error("--create-user requires --name")
    
    if not any([args.email, args.user_id, args.create_user, args.list_users]):
        parser.error("Must specify one of: --email, --user-id, --create-user, or --list-users")
    
    try:
        # Get database session
        db = get_db_session()
        
        if args.list_users:
            list_users(db)
            return
        
        user = None
        
        # Find or create user
        if args.create_user:
            if args.verbose:
                print(f"🔨 Creating new user: {args.email}")
            
            # Check if user already exists
            existing_user = find_user_by_email(db, args.email)
            if existing_user:
                print(f"⚠️  User with email {args.email} already exists!")
                user = existing_user
            else:
                user = create_test_user(db, args.email, args.name, args.role, args.phone)
                print(f"✅ Created new user: {user.name} ({user.email})")
        
        elif args.email:
            if args.verbose:
                print(f"🔍 Finding user by email: {args.email}")
            
            user = find_user_by_email(db, args.email)
            if not user:
                print(f"❌ User with email {args.email} not found!")
                print("💡 Use --create-user to create a new user")
                return
        
        elif args.user_id:
            if args.verbose:
                print(f"🔍 Finding user by ID: {args.user_id}")
            
            user = find_user_by_id(db, args.user_id)
            if not user:
                print(f"❌ User with ID {args.user_id} not found!")
                return
        
        # Generate token
        expires_delta = None
        if args.expires:
            expires_delta = timedelta(minutes=args.expires)
        
        if args.verbose:
            print(f"🔑 Generating token for user: {user.name} ({user.email})")
        
        token = generate_token_for_user(user, expires_delta)
        
        # Format output
        output = format_token_output(user, token, args.format)
        
        # Print output
        if args.format == "json":
            print("\n🎫 Authentication Token Generated:")
            print("=" * 50)
        
        print(output)
        
        if args.format == "json":
            print("=" * 50)
            print("\n💡 Usage Examples:")
            print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/v1/auth/me")
            print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/v1/properties/")
        
        # Save to file if requested
        if args.save:
            with open(args.save, 'w') as f:
                if args.format == "json":
                    f.write(output)
                else:
                    f.write(token)
            print(f"\n💾 Token saved to: {args.save}")
        
        # Show token info
        if args.verbose and args.format != "token":
            print(f"\n📊 Token Info:")
            print(f"  User ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Expires: {args.expires or settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()
