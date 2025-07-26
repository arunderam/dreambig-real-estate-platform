#!/usr/bin/env python3
"""
Test Booking and Investment APIs - DreamBig Real Estate Platform

Tests all booking and investment endpoints including:
- Property bookings (viewing, inspection, etc.)
- Rental applications
- Purchase offers
- Investment management
- Analytics and reporting

Usage:
    python scripts/test_booking_investment_apis.py --verbose
"""

import requests
import json
import time
import argparse
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quick_token import generate_quick_token


class BookingInvestmentAPITester:
    """Test booking and investment API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.results = []
        self.tokens = {}
        self.test_data = {}
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose or level == "ERROR":
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def setup_tokens(self):
        """Generate JWT tokens for testing."""
        self.log("Generating JWT tokens for testing...")
        
        try:
            # Generate tokens for different user types
            tenant_result = generate_quick_token("tenant")
            owner_result = generate_quick_token("owner") 
            admin_result = generate_quick_token("admin")
            
            self.tokens = {
                "tenant": tenant_result["access_token"],
                "owner": owner_result["access_token"],
                "admin": admin_result["access_token"]
            }
            
            self.log(f"✅ Generated JWT tokens for {len(self.tokens)} user types")
            
        except Exception as e:
            self.log(f"❌ Failed to generate tokens: {e}", "ERROR")
            raise
    
    def test_endpoint(self, name: str, method: str, endpoint: str, auth_type: str = None,
                     data: dict = None, params: dict = None,
                     expected_status: int = 200) -> bool:
        """Test a single API endpoint."""
        self.log(f"Testing {name}...")
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Add authentication if specified
        if auth_type and auth_type in self.tokens:
            headers["Authorization"] = f"Bearer {self.tokens[auth_type]}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "test_name": name,
                "method": method.upper(),
                "endpoint": endpoint,
                "auth_type": auth_type,
                "status_code": response.status_code,
                "response_time": round(response_time * 1000, 2),  # ms
                "expected_status": expected_status,
                "success": response.status_code == expected_status
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
                # Store important data for later tests
                if result["success"] and "id" in result["response_data"]:
                    if "booking" in name.lower():
                        self.test_data["booking_id"] = result["response_data"]["id"]
                    elif "investment" in name.lower():
                        self.test_data["investment_id"] = result["response_data"]["id"]
                    elif "application" in name.lower():
                        self.test_data["application_id"] = result["response_data"]["id"]
                    elif "offer" in name.lower():
                        self.test_data["offer_id"] = result["response_data"]["id"]
            except:
                result["response_data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            # Log result
            status_icon = "✅" if result["success"] else "❌"
            self.log(f"{status_icon} {name}: {result['status_code']} ({result['response_time']}ms)")
            
            if not result["success"] and self.verbose:
                self.log(f"   Expected: {expected_status}, Got: {result['status_code']}")
                if isinstance(result["response_data"], str):
                    self.log(f"   Response: {result['response_data'][:100]}")
            
            self.results.append(result)
            return result["success"]
            
        except Exception as e:
            self.log(f"❌ {name}: Error - {str(e)}", "ERROR")
            self.results.append({
                "test_name": name,
                "method": method.upper(),
                "endpoint": endpoint,
                "success": False,
                "error": str(e)
            })
            return False
    
    def test_property_bookings(self):
        """Test property booking endpoints."""
        self.log("\n🏠 Testing Property Booking Endpoints")
        
        # Create a property booking
        booking_date = (datetime.now() + timedelta(days=1)).isoformat()
        booking_data = {
            "property_id": 1,
            "booking_type": "viewing",
            "preferred_date": booking_date,
            "preferred_time": "14:00",
            "duration_minutes": 60,
            "notes": "Interested in viewing this property",
            "contact_name": "Test User",
            "contact_phone": "9876543210",
            "contact_email": "test@example.com"
        }
        
        self.test_endpoint(
            "Create Property Booking",
            "POST", "/api/v1/bookings/property-bookings",
            auth_type="tenant",
            data=booking_data
        )
        
        # Get user's bookings
        self.test_endpoint(
            "Get My Property Bookings",
            "GET", "/api/v1/bookings/property-bookings",
            auth_type="tenant"
        )
        
        # Get upcoming bookings
        self.test_endpoint(
            "Get Upcoming Bookings",
            "GET", "/api/v1/bookings/property-bookings/upcoming",
            auth_type="tenant"
        )
        
        # Get booking analytics
        self.test_endpoint(
            "Get Booking Analytics",
            "GET", "/api/v1/bookings/analytics/bookings",
            auth_type="tenant"
        )
    
    def test_rental_applications(self):
        """Test rental application endpoints."""
        self.log("\n🏘️ Testing Rental Application Endpoints")
        
        # Create rental application
        application_data = {
            "property_id": 1,
            "monthly_income": 50000,
            "employment_status": "employed",
            "references": [
                {
                    "name": "John Doe",
                    "relationship": "employer",
                    "contact": "john@company.com"
                }
            ],
            "additional_info": "Responsible tenant with good credit history"
        }
        
        self.test_endpoint(
            "Create Rental Application",
            "POST", "/api/v1/bookings/rental-applications",
            auth_type="tenant",
            data=application_data
        )
        
        # Get user's rental applications
        self.test_endpoint(
            "Get My Rental Applications",
            "GET", "/api/v1/bookings/rental-applications",
            auth_type="tenant"
        )
    
    def test_purchase_offers(self):
        """Test purchase offer endpoints."""
        self.log("\n💰 Testing Purchase Offer Endpoints")
        
        # Create purchase offer
        offer_data = {
            "property_id": 1,
            "offered_price": 8000000,
            "financing_type": "loan",
            "contingencies": ["inspection", "financing"],
            "closing_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "additional_terms": "Offer valid for 7 days"
        }
        
        self.test_endpoint(
            "Create Purchase Offer",
            "POST", "/api/v1/bookings/purchase-offers",
            auth_type="tenant",
            data=offer_data
        )
        
        # Get user's purchase offers
        self.test_endpoint(
            "Get My Purchase Offers",
            "GET", "/api/v1/bookings/purchase-offers",
            auth_type="tenant"
        )
    
    def test_investments(self):
        """Test investment endpoints."""
        self.log("\n📈 Testing Investment Endpoints")
        
        # Create investment
        investment_data = {
            "title": "Real Estate Investment Fund",
            "amount": 100000,
            "expected_roi": 12.5,
            "investment_type": "real_estate",
            "duration_months": 24,
            "risk_level": "medium",
            "property_id": 1,
            "description": "Investment in premium real estate portfolio"
        }
        
        self.test_endpoint(
            "Create Investment",
            "POST", "/api/v1/investments/",
            auth_type="tenant",
            data=investment_data
        )
        
        # Get user's investments
        self.test_endpoint(
            "Get My Investments",
            "GET", "/api/v1/investments/",
            auth_type="tenant"
        )
        
        # Get specific investment (if created successfully)
        if "investment_id" in self.test_data:
            self.test_endpoint(
                "Get Investment Details",
                "GET", f"/api/v1/investments/{self.test_data['investment_id']}",
                auth_type="tenant"
            )
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        self.log("\n⚠️ Testing Error Handling")
        
        # Test booking non-existent property
        self.test_endpoint(
            "Book Non-existent Property",
            "POST", "/api/v1/bookings/property-bookings",
            auth_type="tenant",
            data={
                "property_id": 99999,
                "booking_type": "viewing",
                "preferred_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "preferred_time": "14:00",
                "duration_minutes": 60,
                "contact_name": "Test User",
                "contact_phone": "9876543210",
                "contact_email": "test@example.com"
            },
            expected_status=404
        )
        
        # Test unauthorized access
        self.test_endpoint(
            "Unauthorized Booking Access",
            "GET", "/api/v1/bookings/property-bookings",
            expected_status=401
        )
        
        # Test invalid investment data
        self.test_endpoint(
            "Invalid Investment Data",
            "POST", "/api/v1/investments/",
            auth_type="tenant",
            data={
                "title": "",  # Invalid empty title
                "amount": -1000,  # Invalid negative amount
                "expected_roi": 12.5,
                "investment_type": "real_estate",
                "duration_months": 24,
                "risk_level": "medium"
            },
            expected_status=422
        )
    
    def run_all_tests(self):
        """Run all booking and investment API tests."""
        self.log("🚀 Starting Booking & Investment API Tests...")
        
        try:
            # Setup JWT tokens
            self.setup_tokens()
            
            # Run test suites
            self.test_property_bookings()
            self.test_rental_applications()
            self.test_purchase_offers()
            self.test_investments()
            self.test_error_handling()
            
            # Generate summary
            self.generate_summary()
            
        except Exception as e:
            self.log(f"❌ Test execution failed: {e}", "ERROR")
            return False
        
        return True
    
    def generate_summary(self):
        """Generate test summary."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        # Calculate average response time for successful tests
        successful_results = [r for r in self.results if r.get("success", False) and "response_time" in r]
        avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results) if successful_results else 0
        
        self.log(f"\n📊 Booking & Investment API Tests Summary:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests} ✅")
        self.log(f"   Failed: {failed_tests} ❌")
        self.log(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        self.log(f"   Average Response Time: {avg_response_time:.2f}ms")
        
        if failed_tests > 0:
            self.log(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result.get("success", False):
                    self.log(f"   - {result['test_name']}: {result.get('status_code', 'Error')}")
        
        # Show feature verification
        self.log(f"\n🔧 Feature Verification:")
        booking_tests = [r for r in self.results if "booking" in r["test_name"].lower() and r.get("success", False)]
        investment_tests = [r for r in self.results if "investment" in r["test_name"].lower() and r.get("success", False)]
        application_tests = [r for r in self.results if "application" in r["test_name"].lower() and r.get("success", False)]
        offer_tests = [r for r in self.results if "offer" in r["test_name"].lower() and r.get("success", False)]
        
        self.log(f"   ✅ Property Bookings: {len(booking_tests)} tests passed")
        self.log(f"   ✅ Investment Management: {len(investment_tests)} tests passed")
        self.log(f"   ✅ Rental Applications: {len(application_tests)} tests passed")
        self.log(f"   ✅ Purchase Offers: {len(offer_tests)} tests passed")


def main():
    parser = argparse.ArgumentParser(description="Test DreamBig Booking & Investment APIs")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Create API tester
    tester = BookingInvestmentAPITester(base_url=args.base_url, verbose=args.verbose)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
