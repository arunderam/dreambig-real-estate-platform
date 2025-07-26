#!/usr/bin/env python3
"""
API Endpoint Testing Script for DreamBig Real Estate Platform

Tests all major API endpoints with generated authentication tokens.

Usage:
    python scripts/test_api_endpoints.py
    python scripts/test_api_endpoints.py --base-url https://api.dreambig.com
    python scripts/test_api_endpoints.py --verbose
"""

import requests
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quick_token import generate_quick_token


class APITester:
    """API endpoint testing class."""
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.tokens = {}
        self.session = requests.Session()
        self.results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose or level == "ERROR":
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def setup_tokens(self):
        """Generate authentication tokens for testing."""
        self.log("Generating authentication tokens...")
        
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
            
            self.log(f"✅ Generated tokens for {len(self.tokens)} user types")
            
        except Exception as e:
            self.log(f"❌ Failed to generate tokens: {e}", "ERROR")
            raise
    
    def make_request(self, method: str, endpoint: str, auth_type: str = None, 
                    data: Dict[Any, Any] = None, params: Dict[str, str] = None) -> Dict[str, Any]:
        """Make HTTP request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Add authentication if specified
        if auth_type and auth_type in self.tokens:
            headers["Authorization"] = f"Bearer {self.tokens[auth_type]}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "url": url,
                "auth_type": auth_type,
                "status_code": response.status_code,
                "response_time": round(response_time * 1000, 2),  # ms
                "success": 200 <= response.status_code < 300,
                "response_size": len(response.content)
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            return result
            
        except Exception as e:
            return {
                "method": method.upper(),
                "endpoint": endpoint,
                "url": url,
                "auth_type": auth_type,
                "status_code": 0,
                "response_time": 0,
                "success": False,
                "error": str(e)
            }
    
    def test_endpoint(self, name: str, method: str, endpoint: str, auth_type: str = None,
                     data: Dict[Any, Any] = None, params: Dict[str, str] = None,
                     expected_status: int = 200) -> bool:
        """Test a single API endpoint."""
        self.log(f"Testing {name}...")
        
        result = self.make_request(method, endpoint, auth_type, data, params)
        result["test_name"] = name
        result["expected_status"] = expected_status
        
        # Check if test passed
        status_match = result["status_code"] == expected_status
        result["test_passed"] = status_match and result["success"]
        
        # Log result
        status_icon = "✅" if result["test_passed"] else "❌"
        self.log(f"{status_icon} {name}: {result['status_code']} ({result['response_time']}ms)")
        
        if not result["test_passed"] and self.verbose:
            self.log(f"   Expected: {expected_status}, Got: {result['status_code']}")
            if "error" in result:
                self.log(f"   Error: {result['error']}")
        
        self.results.append(result)
        return result["test_passed"]
    
    def run_authentication_tests(self):
        """Test authentication endpoints."""
        self.log("\n🔐 Testing Authentication Endpoints")
        
        # Test get current user (should work with token)
        self.test_endpoint(
            "Get Current User (Tenant)",
            "GET", "/api/v1/auth/me",
            auth_type="tenant"
        )
        
        # Test unauthorized access (should fail)
        self.test_endpoint(
            "Get Current User (No Auth)",
            "GET", "/api/v1/auth/me",
            expected_status=401
        )
        
        # Test admin endpoint with admin token
        self.test_endpoint(
            "Admin Users List",
            "GET", "/api/v1/auth/admin/users",
            auth_type="admin"
        )
        
        # Test admin endpoint with regular user (should fail)
        self.test_endpoint(
            "Admin Users List (Forbidden)",
            "GET", "/api/v1/auth/admin/users",
            auth_type="tenant",
            expected_status=403
        )
    
    def run_property_tests(self):
        """Test property endpoints."""
        self.log("\n🏠 Testing Property Endpoints")
        
        # Test get all properties (public)
        self.test_endpoint(
            "Get All Properties",
            "GET", "/api/v1/properties/"
        )
        
        # Test property search
        self.test_endpoint(
            "Search Properties by City",
            "GET", "/api/v1/properties/search",
            params={"city": "Mumbai"}
        )
        
        # Test property search with multiple filters
        self.test_endpoint(
            "Search Properties (Multiple Filters)",
            "GET", "/api/v1/properties/search",
            params={
                "city": "Mumbai",
                "bhk": "3",
                "min_price": "1000000",
                "max_price": "5000000"
            }
        )
        
        # Test create property (owner required)
        property_data = {
            "title": "Test API Property",
            "description": "Property created via API test",
            "price": 3500000.0,
            "bhk": 2,
            "area": 1000.0,
            "property_type": "apartment",
            "furnishing": "furnished",
            "address": "123 Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "latitude": 19.0760,
            "longitude": 72.8777
        }
        
        self.test_endpoint(
            "Create Property (Owner)",
            "POST", "/api/v1/properties/",
            auth_type="owner",
            data=property_data,
            expected_status=201
        )
        
        # Test create property without auth (should fail)
        self.test_endpoint(
            "Create Property (No Auth)",
            "POST", "/api/v1/properties/",
            data=property_data,
            expected_status=401
        )
        
        # Test property recommendations
        self.test_endpoint(
            "Property Recommendations",
            "GET", "/api/v1/properties/recommendations",
            auth_type="tenant"
        )
        
        # Test property comparison
        comparison_data = {"property_ids": [1, 2]}
        self.test_endpoint(
            "Property Comparison",
            "POST", "/api/v1/properties/compare",
            data=comparison_data
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
    
    def run_all_tests(self):
        """Run all API tests."""
        self.log("🚀 Starting API endpoint tests...")
        
        try:
            # Setup authentication tokens
            self.setup_tokens()
            
            # Run test suites
            self.run_authentication_tests()
            self.run_property_tests()
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
        passed_tests = sum(1 for r in self.results if r["test_passed"])
        failed_tests = total_tests - passed_tests
        
        avg_response_time = sum(r["response_time"] for r in self.results) / total_tests if total_tests > 0 else 0
        
        self.log(f"\n📊 Test Summary:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests} ✅")
        self.log(f"   Failed: {failed_tests} ❌")
        self.log(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        self.log(f"   Average Response Time: {avg_response_time:.2f}ms")
        
        if failed_tests > 0:
            self.log(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["test_passed"]:
                    self.log(f"   - {result['test_name']}: {result['status_code']}")
    
    def save_results(self, filename: str = "api_test_results.json"):
        """Save test results to file."""
        output_path = Path(filename)
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r["test_passed"]),
            "failed_tests": sum(1 for r in self.results if not r["test_passed"]),
            "results": self.results
        }
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"💾 Test results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Test DreamBig API endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--save-results", action="store_true",
                       help="Save test results to JSON file")
    
    args = parser.parse_args()
    
    # Create API tester
    tester = APITester(base_url=args.base_url, verbose=args.verbose)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Save results if requested
    if args.save_results:
        tester.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
