#!/usr/bin/env python3
"""
Test Fixed API Endpoints - DreamBig Real Estate Platform

Tests all the API endpoints that have been fixed, including:
- JWT authentication support
- Missing admin endpoints
- Missing property endpoints
- Correct endpoint paths

Usage:
    python scripts/test_fixed_apis.py --verbose
"""

import requests
import json
import time
import argparse
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quick_token import generate_quick_token


class FixedAPITester:
    """Test fixed API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.results = []
        self.tokens = {}
    
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
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params)
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
    
    def test_jwt_authentication(self):
        """Test JWT authentication functionality."""
        self.log("\n🔐 Testing JWT Authentication")
        
        # Test with tenant token
        self.test_endpoint(
            "JWT Auth - Tenant Token",
            "GET", "/api/v1/properties/1",
            auth_type="tenant"
        )
        
        # Test with owner token
        self.test_endpoint(
            "JWT Auth - Owner Token", 
            "GET", "/api/v1/properties/1",
            auth_type="owner"
        )
        
        # Test without token (should still work for public endpoints)
        self.test_endpoint(
            "No Auth - Public Endpoint",
            "GET", "/api/v1/properties/1"
        )
    
    def test_admin_endpoints(self):
        """Test admin endpoints."""
        self.log("\n👑 Testing Admin Endpoints")
        
        # Test admin users list
        self.test_endpoint(
            "Admin - Get All Users",
            "GET", "/api/v1/auth/admin/users",
            auth_type="admin"
        )
        
        # Test admin users list with pagination
        self.test_endpoint(
            "Admin - Get Users (Paginated)",
            "GET", "/api/v1/auth/admin/users",
            auth_type="admin",
            params={"skip": "0", "limit": "5"}
        )
        
        # Test get specific user by ID
        self.test_endpoint(
            "Admin - Get User by ID",
            "GET", "/api/v1/auth/admin/users/1",
            auth_type="admin"
        )
        
        # Test admin endpoint with non-admin user (should fail)
        self.test_endpoint(
            "Admin - Forbidden Access",
            "GET", "/api/v1/auth/admin/users",
            auth_type="tenant",
            expected_status=403
        )
    
    def test_property_endpoints(self):
        """Test property endpoints."""
        self.log("\n🏠 Testing Property Endpoints")
        
        # Test property recommendations
        self.test_endpoint(
            "Property Recommendations",
            "GET", "/api/v1/properties/recommendations"
        )
        
        # Test property recommendations with auth
        self.test_endpoint(
            "Property Recommendations (Authenticated)",
            "GET", "/api/v1/properties/recommendations",
            auth_type="tenant"
        )
        
        # Test property comparison
        self.test_endpoint(
            "Property Comparison",
            "POST", "/api/v1/properties/compare",
            data={"property_ids": [1, 2, 3]}
        )
        
        # Test property search (new endpoint)
        self.test_endpoint(
            "Property Search (New Endpoint)",
            "GET", "/api/v1/properties/search",
            params={"city": "Mumbai", "bhk": "3"}
        )
        
        # Test property search with price filter
        self.test_endpoint(
            "Property Search (Price Filter)",
            "GET", "/api/v1/properties/search",
            params={"min_price": "1000000", "max_price": "10000000"}
        )
    
    def test_endpoint_paths(self):
        """Test correct endpoint paths."""
        self.log("\n🛣️  Testing Endpoint Paths")
        
        # Test original search endpoint (should still work)
        self.test_endpoint(
            "Original Search Endpoint",
            "GET", "/api/v1/search/",
            params={"location": "Mumbai"}
        )
        
        # Test new property search endpoint
        self.test_endpoint(
            "New Property Search Endpoint",
            "GET", "/api/v1/properties/search",
            params={"city": "Mumbai"}
        )
        
        # Test property by ID (should work without auth now)
        self.test_endpoint(
            "Property by ID (Public)",
            "GET", "/api/v1/properties/1"
        )
    
    def test_error_handling(self):
        """Test error handling."""
        self.log("\n⚠️  Testing Error Handling")
        
        # Test non-existent property
        self.test_endpoint(
            "Non-existent Property",
            "GET", "/api/v1/properties/99999",
            expected_status=404
        )
        
        # Test invalid comparison (too few properties)
        self.test_endpoint(
            "Invalid Comparison (Too Few)",
            "POST", "/api/v1/properties/compare",
            data={"property_ids": [1]},
            expected_status=400
        )
        
        # Test invalid comparison (too many properties)
        self.test_endpoint(
            "Invalid Comparison (Too Many)",
            "POST", "/api/v1/properties/compare",
            data={"property_ids": [1, 2, 3, 4, 5, 6]},
            expected_status=400
        )
    
    def run_all_tests(self):
        """Run all fixed API tests."""
        self.log("🚀 Starting Fixed API Tests...")
        
        try:
            # Setup JWT tokens
            self.setup_tokens()
            
            # Run test suites
            self.test_jwt_authentication()
            self.test_admin_endpoints()
            self.test_property_endpoints()
            self.test_endpoint_paths()
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
        
        self.log(f"\n📊 Fixed API Tests Summary:")
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
        
        # Show fixes verification
        self.log(f"\n🔧 Fixes Verification:")
        jwt_tests = [r for r in self.results if "JWT Auth" in r["test_name"] and r.get("success", False)]
        admin_tests = [r for r in self.results if "Admin" in r["test_name"] and r.get("success", False)]
        property_tests = [r for r in self.results if "Property" in r["test_name"] and r.get("success", False)]
        
        self.log(f"   ✅ JWT Authentication: {len(jwt_tests)} tests passed")
        self.log(f"   ✅ Admin Endpoints: {len(admin_tests)} tests passed")
        self.log(f"   ✅ Property Endpoints: {len(property_tests)} tests passed")


def main():
    parser = argparse.ArgumentParser(description="Test fixed DreamBig API endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Create API tester
    tester = FixedAPITester(base_url=args.base_url, verbose=args.verbose)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
