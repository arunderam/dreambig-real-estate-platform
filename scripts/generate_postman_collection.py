#!/usr/bin/env python3
"""
Postman Collection Generator for DreamBig Real Estate Platform

Generates a Postman collection with pre-configured requests and authentication tokens.

Usage:
    python scripts/generate_postman_collection.py
    python scripts/generate_postman_collection.py --output dreambig_api.json
    python scripts/generate_postman_collection.py --base-url https://api.dreambig.com
"""

import json
import uuid
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to Python path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quick_token import generate_quick_token


def generate_postman_collection(base_url="http://localhost:8000", include_tokens=True):
    """Generate Postman collection for DreamBig API."""
    
    # Generate tokens for different user types
    tokens = {}
    if include_tokens:
        try:
            tokens["tenant"] = generate_quick_token("tenant")["access_token"]
            tokens["owner"] = generate_quick_token("owner")["access_token"]
            tokens["admin"] = generate_quick_token("admin")["access_token"]
        except Exception as e:
            print(f"⚠️  Warning: Could not generate tokens: {e}")
            include_tokens = False
    
    collection = {
        "info": {
            "name": "DreamBig Real Estate Platform API",
            "description": "Complete API collection for DreamBig Real Estate Platform with authentication tokens",
            "version": "1.0.0",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": tokens.get("tenant", "{{tenant_token}}"),
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": base_url,
                "type": "string"
            },
            {
                "key": "tenant_token",
                "value": tokens.get("tenant", ""),
                "type": "string"
            },
            {
                "key": "owner_token", 
                "value": tokens.get("owner", ""),
                "type": "string"
            },
            {
                "key": "admin_token",
                "value": tokens.get("admin", ""),
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Authentication endpoints
    auth_folder = {
        "name": "Authentication",
        "description": "User authentication and profile management",
        "item": [
            {
                "name": "Register User",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "newuser@example.com",
                            "name": "New User",
                            "phone": "+1234567890",
                            "role": "tenant",
                            "preferences": {
                                "budget_min": 1000000,
                                "budget_max": 5000000,
                                "preferred_locations": ["Mumbai", "Delhi"]
                            }
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/auth/register",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "auth", "register"]
                    }
                }
            },
            {
                "name": "Login",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "firebase_token": "your_firebase_token_here"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/auth/login",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "auth", "login"]
                    }
                }
            },
            {
                "name": "Get Current User",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/api/v1/auth/me",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "auth", "me"]
                    }
                }
            },
            {
                "name": "Update Profile",
                "request": {
                    "method": "PUT",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "name": "Updated Name",
                            "phone": "+9876543210",
                            "preferences": {
                                "budget_min": 2000000,
                                "budget_max": 8000000,
                                "preferred_locations": ["Bangalore", "Chennai"]
                            }
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/auth/profile",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "auth", "profile"]
                    }
                }
            },
            {
                "name": "Forgot Password",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "user@example.com"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/auth/forgot-password",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "auth", "forgot-password"]
                    }
                }
            }
        ]
    }
    
    # Properties endpoints
    properties_folder = {
        "name": "Properties",
        "description": "Property management and search",
        "item": [
            {
                "name": "Get All Properties",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", ""]
                    }
                }
            },
            {
                "name": "Create Property",
                "request": {
                    "auth": {
                        "type": "bearer",
                        "bearer": [
                            {
                                "key": "token",
                                "value": "{{owner_token}}",
                                "type": "string"
                            }
                        ]
                    },
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "title": "Beautiful 3BHK Apartment",
                            "description": "Spacious apartment with modern amenities",
                            "price": 5000000.0,
                            "bhk": 3,
                            "area": 1200.0,
                            "property_type": "apartment",
                            "furnishing": "semi_furnished",
                            "address": "123 Dream Street",
                            "city": "Mumbai",
                            "state": "Maharashtra",
                            "pincode": "400001",
                            "latitude": 19.0760,
                            "longitude": 72.8777,
                            "amenities": ["parking", "gym", "swimming_pool"]
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", ""]
                    }
                }
            },
            {
                "name": "Get Property by ID",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/1",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", "1"]
                    }
                }
            },
            {
                "name": "Search Properties",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/search?city=Mumbai&bhk=3&min_price=1000000&max_price=5000000",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", "search"],
                        "query": [
                            {
                                "key": "city",
                                "value": "Mumbai"
                            },
                            {
                                "key": "bhk",
                                "value": "3"
                            },
                            {
                                "key": "min_price",
                                "value": "1000000"
                            },
                            {
                                "key": "max_price",
                                "value": "5000000"
                            }
                        ]
                    }
                }
            },
            {
                "name": "Update Property",
                "request": {
                    "auth": {
                        "type": "bearer",
                        "bearer": [
                            {
                                "key": "token",
                                "value": "{{owner_token}}",
                                "type": "string"
                            }
                        ]
                    },
                    "method": "PUT",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "title": "Updated Property Title",
                            "price": 5500000.0,
                            "description": "Updated description"
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/1",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", "1"]
                    }
                }
            },
            {
                "name": "Property Recommendations",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/recommendations",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", "recommendations"]
                    }
                }
            },
            {
                "name": "Property Comparison",
                "request": {
                    "method": "POST",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "property_ids": [1, 2, 3]
                        }, indent=2)
                    },
                    "url": {
                        "raw": "{{base_url}}/api/v1/properties/compare",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "properties", "compare"]
                    }
                }
            }
        ]
    }
    
    # Admin endpoints
    admin_folder = {
        "name": "Admin",
        "description": "Admin-only endpoints",
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{admin_token}}",
                    "type": "string"
                }
            ]
        },
        "item": [
            {
                "name": "Get All Users",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/api/v1/auth/admin/users",
                        "host": ["{{base_url}}"],
                        "path": ["api", "v1", "auth", "admin", "users"]
                    }
                }
            }
        ]
    }
    
    # Add folders to collection
    collection["item"] = [auth_folder, properties_folder, admin_folder]
    
    return collection


def main():
    parser = argparse.ArgumentParser(description="Generate Postman collection for DreamBig API")
    parser.add_argument("--output", "-o", default="DreamBig_API.postman_collection.json",
                       help="Output file name (default: DreamBig_API.postman_collection.json)")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--no-tokens", action="store_true",
                       help="Don't generate authentication tokens")
    
    args = parser.parse_args()
    
    try:
        print("🚀 Generating Postman collection...")
        
        # Generate collection
        collection = generate_postman_collection(
            base_url=args.base_url,
            include_tokens=not args.no_tokens
        )
        
        # Save to file
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(collection, f, indent=2)
        
        print(f"✅ Postman collection generated: {output_path}")
        print(f"📊 Collection contains {len(collection['item'])} folders")
        
        # Count total requests
        total_requests = sum(len(folder['item']) for folder in collection['item'])
        print(f"🔗 Total API requests: {total_requests}")
        
        if not args.no_tokens:
            print(f"🎫 Authentication tokens included for testing")
        
        print(f"\n💡 Import this file into Postman to start testing the API!")
        print(f"   File: {output_path.absolute()}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
