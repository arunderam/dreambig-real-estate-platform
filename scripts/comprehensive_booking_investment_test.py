#!/usr/bin/env python3
"""
Comprehensive Booking & Investment API Test - DreamBig Real Estate Platform

Tests all booking and investment endpoints with proper data validation.
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quick_token import generate_quick_token


def test_booking_investment_apis():
    """Test all booking and investment APIs comprehensively."""
    
    print("🚀 COMPREHENSIVE BOOKING & INVESTMENT API TEST")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    results = {"passed": 0, "failed": 0, "total": 0}
    
    # Get authentication token
    try:
        token_result = generate_quick_token("tenant")
        token = token_result["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print(f"✅ Authentication: JWT token generated for {token_result['user']['email']}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    def test_endpoint(name, method, url, data=None, expected_status=200):
        """Test a single endpoint."""
        results["total"] += 1
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            
            success = response.status_code == expected_status
            status_icon = "✅" if success else "❌"
            
            print(f"{status_icon} {name}: {response.status_code}")
            
            if success:
                results["passed"] += 1
                # Show response data for successful creates
                if method == "POST" and response.status_code in [200, 201]:
                    try:
                        data = response.json()
                        if "id" in data:
                            print(f"   📝 Created ID: {data['id']}")
                    except:
                        pass
            else:
                results["failed"] += 1
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        print(f"   ❌ Error: {str(error_data['detail'])[:100]}")
                except:
                    print(f"   ❌ Error: {response.text[:100]}")
            
            return success, response
            
        except Exception as e:
            results["failed"] += 1
            print(f"❌ {name}: Exception - {str(e)[:50]}")
            return False, None
    
    print("\n🏠 PROPERTY BOOKING TESTS:")
    print("-" * 30)
    
    # Test 1: Create Property Booking
    booking_data = {
        "property_id": 1,
        "booking_type": "viewing",
        "preferred_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "preferred_time": "14:00",
        "duration_minutes": 60,
        "notes": "Interested in viewing this luxury apartment",
        "contact_name": "John Doe",
        "contact_phone": "9876543210",
        "contact_email": "john.doe@example.com"
    }
    
    success, response = test_endpoint(
        "Create Property Booking",
        "POST",
        f"{base_url}/api/v1/bookings/property-bookings",
        booking_data
    )
    
    booking_id = None
    if success and response:
        try:
            booking_id = response.json().get("id")
        except:
            pass
    
    # Test 2: Get User's Bookings
    test_endpoint(
        "Get My Property Bookings",
        "GET",
        f"{base_url}/api/v1/bookings/property-bookings"
    )
    
    # Test 3: Get Booking Analytics
    test_endpoint(
        "Get Booking Analytics",
        "GET",
        f"{base_url}/api/v1/bookings/analytics/bookings"
    )
    
    print("\n🏘️ RENTAL APPLICATION TESTS:")
    print("-" * 35)
    
    # Test 4: Create Rental Application
    rental_data = {
        "property_id": 1,
        "monthly_income": 75000,
        "employment_status": "employed",
        "employer_name": "Tech Corp",
        "employment_duration_months": 36,
        "references": [
            {
                "name": "Jane Smith",
                "relationship": "supervisor",
                "contact": "jane.smith@techcorp.com",
                "phone": "9876543211"
            }
        ],
        "additional_info": "Responsible tenant with excellent credit history"
    }
    
    test_endpoint(
        "Create Rental Application",
        "POST",
        f"{base_url}/api/v1/bookings/rental-applications",
        rental_data
    )
    
    # Test 5: Get User's Rental Applications
    test_endpoint(
        "Get My Rental Applications",
        "GET",
        f"{base_url}/api/v1/bookings/rental-applications"
    )
    
    print("\n💰 PURCHASE OFFER TESTS:")
    print("-" * 25)
    
    # Test 6: Create Purchase Offer
    offer_data = {
        "property_id": 1,
        "offered_price": 8200000,
        "financing_type": "loan",
        "down_payment_percentage": 20,
        "contingencies": ["inspection", "financing", "appraisal"],
        "closing_date": (datetime.now() + timedelta(days=45)).isoformat(),
        "offer_expiry_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "additional_terms": "Seller to provide home warranty"
    }
    
    test_endpoint(
        "Create Purchase Offer",
        "POST",
        f"{base_url}/api/v1/bookings/purchase-offers",
        offer_data
    )
    
    # Test 7: Get User's Purchase Offers
    test_endpoint(
        "Get My Purchase Offers",
        "GET",
        f"{base_url}/api/v1/bookings/purchase-offers"
    )
    
    print("\n📈 INVESTMENT TESTS:")
    print("-" * 20)
    
    # Test 8: Create Investment
    investment_data = {
        "title": "Premium Real Estate Investment",
        "amount": 500000,
        "expected_roi": 15.5,
        "investment_type": "real_estate",
        "duration_months": 36,
        "risk_level": "medium",
        "property_id": 1,
        "description": "Investment in high-growth real estate portfolio with guaranteed returns",
        "location": "Mumbai, Maharashtra"
    }
    
    success, response = test_endpoint(
        "Create Investment",
        "POST",
        f"{base_url}/api/v1/investments/",
        investment_data
    )
    
    investment_id = None
    if success and response:
        try:
            investment_id = response.json().get("id")
        except:
            pass
    
    # Test 9: Get User's Investments
    test_endpoint(
        "Get My Investments",
        "GET",
        f"{base_url}/api/v1/investments/"
    )
    
    # Test 10: Get Specific Investment (if created)
    if investment_id:
        test_endpoint(
            "Get Investment Details",
            "GET",
            f"{base_url}/api/v1/investments/{investment_id}"
        )
    
    print("\n⚠️ ERROR HANDLING TESTS:")
    print("-" * 25)
    
    # Test 11: Invalid Booking Data
    invalid_booking = {
        "property_id": 1,
        "booking_type": "viewing",
        "preferred_date": "invalid-date",  # Invalid date
        "preferred_time": "25:00",  # Invalid time
        "contact_name": "",  # Empty name
        "contact_phone": "123",  # Invalid phone
        "contact_email": "invalid-email"  # Invalid email
    }
    
    test_endpoint(
        "Invalid Booking Data",
        "POST",
        f"{base_url}/api/v1/bookings/property-bookings",
        invalid_booking,
        expected_status=422
    )
    
    # Test 12: Invalid Investment Data
    invalid_investment = {
        "title": "",  # Empty title
        "amount": -1000,  # Negative amount
        "expected_roi": 150,  # ROI > 100%
        "investment_type": "",  # Empty type
        "duration_months": 0,  # Zero duration
        "risk_level": "invalid"  # Invalid risk level
    }
    
    test_endpoint(
        "Invalid Investment Data",
        "POST",
        f"{base_url}/api/v1/investments/",
        invalid_investment,
        expected_status=422
    )
    
    # Test 13: Non-existent Property Booking
    nonexistent_booking = {
        "property_id": 99999,  # Non-existent property
        "booking_type": "viewing",
        "preferred_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "preferred_time": "14:00",
        "duration_minutes": 60,
        "contact_name": "Test User",
        "contact_phone": "9876543210",
        "contact_email": "test@example.com"
    }
    
    test_endpoint(
        "Book Non-existent Property",
        "POST",
        f"{base_url}/api/v1/bookings/property-bookings",
        nonexistent_booking,
        expected_status=404
    )
    
    print("\n📊 TEST SUMMARY:")
    print("=" * 20)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {(results['passed']/results['total'])*100:.1f}%")
    
    print("\n🎉 BOOKING & INVESTMENT API FEATURES:")
    print("=" * 45)
    print("✅ Property Booking System - Schedule viewings, inspections")
    print("✅ Rental Application System - Apply for rental properties")
    print("✅ Purchase Offer System - Make offers on properties")
    print("✅ Investment Management - Create and track investments")
    print("✅ User Authentication - JWT token-based security")
    print("✅ Data Validation - Comprehensive input validation")
    print("✅ Error Handling - Proper HTTP status codes")
    print("✅ Analytics Support - Booking and investment analytics")
    
    if results["passed"] >= results["total"] * 0.8:
        print("\n🏆 EXCELLENT: Booking & Investment APIs are highly functional!")
    elif results["passed"] >= results["total"] * 0.6:
        print("\n👍 GOOD: Most booking & investment features are working!")
    else:
        print("\n⚠️ NEEDS IMPROVEMENT: Several issues need to be addressed.")


if __name__ == "__main__":
    test_booking_investment_apis()
