#!/usr/bin/env python3
"""
Test Working API Endpoints - DreamBig Real Estate Platform

Tests the API endpoints that are currently working without authentication issues.

Usage:
    python scripts/test_working_apis.py
    python scripts/test_working_apis.py --verbose
"""

import requests
import json
import time
import argparse
from typing import Dict, Any


class WorkingAPITester:
    """Test working API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose or level == "ERROR":
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Dict[Any, Any] = None, params: Dict[str, str] = None,
                     expected_status: int = 200) -> bool:
        """Test a single API endpoint."""
        self.log(f"Testing {name}...")
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "test_name": name,
                "method": method.upper(),
                "endpoint": endpoint,
                "url": url,
                "status_code": response.status_code,
                "response_time": round(response_time * 1000, 2),  # ms
                "expected_status": expected_status,
                "success": response.status_code == expected_status
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            # Log result
            status_icon = "✅" if result["success"] else "❌"
            self.log(f"{status_icon} {name}: {result['status_code']} ({result['response_time']}ms)")
            
            if not result["success"] and self.verbose:
                self.log(f"   Expected: {expected_status}, Got: {result['status_code']}")
            
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
    
    def run_property_tests(self):
        """Test property endpoints."""
        self.log("\n🏠 Testing Property Endpoints")
        
        # Test get all properties
        self.test_endpoint(
            "Get All Properties",
            "GET", "/api/v1/properties/"
        )
        
        # Test get properties with pagination
        self.test_endpoint(
            "Get Properties (Paginated)",
            "GET", "/api/v1/properties/",
            params={"skip": "0", "limit": "5"}
        )
    
    def run_search_tests(self):
        """Test search endpoints."""
        self.log("\n🔍 Testing Search Endpoints")
        
        # Test basic search
        self.test_endpoint(
            "Search Properties (Basic)",
            "GET", "/api/v1/search/"
        )
        
        # Test search by location
        self.test_endpoint(
            "Search by Location",
            "GET", "/api/v1/search/",
            params={"location": "Mumbai"}
        )
        
        # Test search by price range
        self.test_endpoint(
            "Search by Price Range",
            "GET", "/api/v1/search/",
            params={"price_min": "1000000", "price_max": "10000000"}
        )
        
        # Test search by BHK
        self.test_endpoint(
            "Search by BHK",
            "GET", "/api/v1/search/",
            params={"bhk": "3"}
        )
        
        # Test search by property type
        self.test_endpoint(
            "Search by Property Type",
            "GET", "/api/v1/search/",
            params={"property_type": "apartment"}
        )
        
        # Test complex search
        self.test_endpoint(
            "Complex Search",
            "GET", "/api/v1/search/",
            params={
                "location": "Mumbai",
                "bhk": "3",
                "price_min": "5000000",
                "price_max": "15000000",
                "property_type": "apartment"
            }
        )
    
    def run_auth_tests(self):
        """Test authentication endpoints that work."""
        self.log("\n🔐 Testing Authentication Endpoints")
        
        # Test user registration (should handle existing user)
        self.test_endpoint(
            "Test Registration (Existing User)",
            "POST", "/api/v1/auth/test-register",
            data={
                "email": "tenant@dreambig.com",
                "name": "Test Tenant",
                "role": "tenant",
                "password": "testpass123"
            }
        )
        
        # Test user registration (new user)
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_endpoint(
            "Test Registration (New User)",
            "POST", "/api/v1/auth/test-register",
            data={
                "email": unique_email,
                "name": "New Test User",
                "role": "tenant",
                "password": "testpass123"
            }
        )
    
    def run_performance_tests(self):
        """Test API performance."""
        self.log("\n⚡ Testing API Performance")
        
        # Test multiple rapid requests
        start_time = time.time()
        for i in range(5):
            self.test_endpoint(
                f"Performance Test {i+1}",
                "GET", "/api/v1/properties/"
            )
        total_time = time.time() - start_time
        
        self.log(f"📊 5 requests completed in {total_time:.2f}s (avg: {total_time/5:.2f}s)")
        
        # Test search performance
        search_start = time.time()
        for i in range(3):
            self.test_endpoint(
                f"Search Performance Test {i+1}",
                "GET", "/api/v1/search/",
                params={"location": "Mumbai"}
            )
        search_time = time.time() - search_start
        
        self.log(f"🔍 3 search requests completed in {search_time:.2f}s (avg: {search_time/3:.2f}s)")
    
    def run_all_tests(self):
        """Run all working API tests."""
        self.log("🚀 Starting Working API Tests...")
        
        try:
            # Run test suites
            self.run_property_tests()
            self.run_search_tests()
            self.run_auth_tests()
            self.run_performance_tests()
            
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
        
        self.log(f"\n📊 Test Summary:")
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
        
        # Show some sample data
        self.log(f"\n📋 Sample API Responses:")
        for result in self.results[:3]:  # Show first 3 successful tests
            if result.get("success", False) and isinstance(result.get("response_data"), dict):
                self.log(f"   {result['test_name']}:")
                if "properties" in result["response_data"]:
                    properties = result["response_data"]["properties"]
                    self.log(f"     Found {len(properties)} properties")
                    if properties:
                        self.log(f"     Sample: {properties[0].get('title', 'N/A')}")
                elif isinstance(result["response_data"], list) and result["response_data"]:
                    self.log(f"     Found {len(result['response_data'])} items")
                    self.log(f"     Sample: {result['response_data'][0].get('title', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="Test working DreamBig API endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Create API tester
    tester = WorkingAPITester(base_url=args.base_url, verbose=args.verbose)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
