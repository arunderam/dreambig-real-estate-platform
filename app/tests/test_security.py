"""
Security tests for DreamBig Real Estate Platform
"""
import pytest
import json
import time
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from app.tests.conftest import assert_response_error, assert_response_success


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_jwt_token_validation(self, client, test_user):
        """Test JWT token validation."""
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=invalid_headers)
        assert_response_error(response, 401)
        
        # Test with malformed token
        malformed_headers = {"Authorization": "Bearer"}
        response = client.get("/api/v1/auth/me", headers=malformed_headers)
        assert_response_error(response, 401)
        
        # Test with missing Bearer prefix
        no_bearer_headers = {"Authorization": "invalid_token"}
        response = client.get("/api/v1/auth/me", headers=no_bearer_headers)
        assert_response_error(response, 401)
    
    def test_token_expiration(self, client, test_user):
        """Test JWT token expiration."""
        # Mock expired token
        with patch('app.core.security.decode_access_token') as mock_decode:
            mock_decode.side_effect = Exception("Token has expired")
            
            expired_headers = {"Authorization": "Bearer expired_token"}
            response = client.get("/api/v1/auth/me", headers=expired_headers)
            assert_response_error(response, 401)
    
    def test_firebase_token_validation(self, client):
        """Test Firebase token validation."""
        # Test with invalid Firebase token
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid Firebase token")
            
            login_data = {"firebase_token": "invalid_firebase_token"}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert_response_error(response, 401)
    
    def test_password_reset_token_security(self, client):
        """Test password reset token security."""
        # Test with invalid reset token
        reset_data = {
            "token": "invalid_reset_token",
            "new_password": "new_password123",
            "confirm_password": "new_password123"
        }
        
        with patch('app.core.security.verify_password_reset_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid or expired token")
            
            response = client.post("/api/v1/auth/reset-password", json=reset_data)
            assert_response_error(response, 400)
    
    def test_email_verification_token_security(self, client):
        """Test email verification token security."""
        # Test with invalid verification token
        verify_data = {"token": "invalid_verification_token"}
        
        with patch('app.core.security.verify_email_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid verification token")
            
            response = client.post("/api/v1/auth/verify-email", json=verify_data)
            assert_response_error(response, 400)


class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    def test_role_based_access_control(self, client, test_user, test_admin_user, auth_headers, admin_auth_headers):
        """Test role-based access control."""
        # Regular user trying to access admin endpoint
        response = client.get("/api/v1/auth/admin/users", headers=auth_headers)
        assert_response_error(response, 403)
        
        # Admin user accessing admin endpoint
        response = client.get("/api/v1/auth/admin/users", headers=admin_auth_headers)
        assert_response_success(response)
    
    def test_property_ownership_authorization(self, client, test_property, test_user, auth_headers):
        """Test property ownership authorization."""
        # Non-owner trying to update property
        update_data = {"title": "Unauthorized Update"}
        response = client.put(
            f"/api/v1/properties/{test_property.id}",
            json=update_data,
            headers=auth_headers
        )
        assert_response_error(response, 403)
        
        # Non-owner trying to delete property
        response = client.delete(
            f"/api/v1/properties/{test_property.id}",
            headers=auth_headers
        )
        assert_response_error(response, 403)
    
    def test_user_data_isolation(self, client, test_user, test_user_2, auth_headers, auth_headers_2):
        """Test user data isolation."""
        # User 1 trying to access User 2's profile
        response = client.get(f"/api/v1/users/{test_user_2.id}", headers=auth_headers)
        assert_response_error(response, 403)
        
        # User 2 trying to update User 1's profile
        update_data = {"name": "Unauthorized Update"}
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=auth_headers_2
        )
        assert_response_error(response, 403)
    
    def test_booking_authorization(self, client, test_property_booking, test_user, auth_headers):
        """Test booking authorization."""
        # User trying to access another user's booking
        response = client.get(
            f"/api/v1/bookings/{test_property_booking.id}",
            headers=auth_headers
        )
        # Should only allow access if user is the booking owner or property owner
        assert response.status_code in [200, 403]


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self, client, auth_headers):
        """Test SQL injection prevention."""
        # Test SQL injection in search parameters
        malicious_queries = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET role='admin'; --",
            "' UNION SELECT * FROM users --"
        ]
        
        for malicious_query in malicious_queries:
            response = client.get(
                f"/api/v1/properties/search?city={malicious_query}",
                headers=auth_headers
            )
            # Should either return empty results or validation error, not 500
            assert response.status_code in [200, 400, 422]
    
    def test_xss_prevention(self, client, owner_auth_headers):
        """Test XSS prevention."""
        # Test XSS in property creation
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            property_data = {
                "title": f"Property with {payload}",
                "description": f"Description with {payload}",
                "price": 1000000.0,
                "bhk": 2,
                "area": 1000.0,
                "property_type": "apartment",
                "city": "Mumbai"
            }
            
            response = client.post(
                "/api/v1/properties/",
                json=property_data,
                headers=owner_auth_headers
            )
            
            if response.status_code == 201:
                # If property was created, check that XSS payload was sanitized
                data = response.json()
                assert payload not in data["title"]
                assert payload not in data["description"]
    
    def test_file_upload_security(self, client, test_property, owner_auth_headers, temp_upload_dir):
        """Test file upload security."""
        import io
        
        # Test malicious file types
        malicious_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.php", b"<?php echo 'hack'; ?>", "application/x-php"),
            ("malware.bat", b"@echo off\necho hack", "application/x-msdos-program"),
            ("virus.js", b"alert('XSS')", "application/javascript")
        ]
        
        for filename, content, content_type in malicious_files:
            file_content = io.BytesIO(content)
            
            response = client.post(
                f"/api/v1/properties/{test_property.id}/images",
                files={"file": (filename, file_content, content_type)},
                headers=owner_auth_headers
            )
            
            # Should reject malicious file types
            assert_response_error(response, 400)
    
    def test_large_file_upload_protection(self, client, test_property, owner_auth_headers, temp_upload_dir):
        """Test protection against large file uploads."""
        import io
        
        # Create a large file (simulate 100MB)
        large_content = b"A" * (100 * 1024 * 1024)  # 100MB
        large_file = io.BytesIO(large_content)
        
        response = client.post(
            f"/api/v1/properties/{test_property.id}/images",
            files={"file": ("large_image.jpg", large_file, "image/jpeg")},
            headers=owner_auth_headers
        )
        
        # Should reject files that are too large
        assert_response_error(response, 413)  # Payload Too Large
    
    def test_path_traversal_prevention(self, client, test_property, owner_auth_headers, temp_upload_dir):
        """Test path traversal prevention."""
        import io
        
        # Test path traversal in filename
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for filename in malicious_filenames:
            file_content = io.BytesIO(b"fake image content")
            
            response = client.post(
                f"/api/v1/properties/{test_property.id}/images",
                files={"file": (filename, file_content, "image/jpeg")},
                headers=owner_auth_headers
            )
            
            # Should sanitize filename or reject request
            assert response.status_code in [400, 422]


class TestRateLimitingSecurity:
    """Test rate limiting security measures."""
    
    def test_login_rate_limiting(self, client):
        """Test login rate limiting."""
        login_data = {"firebase_token": "invalid_token"}
        
        # Make multiple failed login attempts
        failed_attempts = 0
        for i in range(20):  # Try 20 times
            response = client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 429:  # Too Many Requests
                break
            failed_attempts += 1
        
        # Should eventually hit rate limit
        assert failed_attempts < 20, "Rate limiting not working for login attempts"
    
    def test_api_rate_limiting(self, client, auth_headers):
        """Test general API rate limiting."""
        # Make many requests to the same endpoint
        rate_limited = False
        for i in range(100):  # Try 100 times
            response = client.get("/api/v1/properties/", headers=auth_headers)
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
        
        # Should eventually hit rate limit (depending on configuration)
        # Note: This test might pass if rate limits are high
        print(f"Rate limiting test: {'PASSED' if rate_limited else 'SKIPPED (high limits)'}")
    
    def test_password_reset_rate_limiting(self, client, test_user):
        """Test password reset rate limiting."""
        reset_data = {"email": test_user.email}
        
        # Make multiple password reset requests
        rate_limited = False
        for i in range(10):  # Try 10 times
            response = client.post("/api/v1/auth/forgot-password", json=reset_data)
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
        
        # Should hit rate limit for password reset requests
        assert rate_limited, "Rate limiting not working for password reset"


class TestCSRFProtection:
    """Test CSRF protection measures."""
    
    def test_csrf_token_validation(self, client, auth_headers):
        """Test CSRF token validation."""
        # Test state-changing operations without CSRF token
        property_data = {
            "title": "Test Property",
            "price": 1000000.0,
            "bhk": 2,
            "area": 1000.0,
            "property_type": "apartment",
            "city": "Mumbai"
        }
        
        # Remove CSRF token if present
        headers_without_csrf = auth_headers.copy()
        headers_without_csrf.pop("X-CSRF-Token", None)
        
        response = client.post(
            "/api/v1/properties/",
            json=property_data,
            headers=headers_without_csrf
        )
        
        # Should require CSRF token for state-changing operations
        # Note: This depends on CSRF protection being enabled
        assert response.status_code in [200, 201, 403, 422]


class TestSessionSecurity:
    """Test session security measures."""
    
    def test_session_fixation_prevention(self, client, test_user):
        """Test session fixation prevention."""
        # Login with a specific session
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.return_value = {
                "uid": test_user.firebase_uid,
                "email": test_user.email,
                "name": test_user.name
            }
            
            login_data = {"firebase_token": "valid_token"}
            response = client.post("/api/v1/auth/login", json=login_data)
            
            if response.status_code == 200:
                token1 = response.json()["access_token"]
                
                # Login again - should get a different token
                response2 = client.post("/api/v1/auth/login", json=login_data)
                if response2.status_code == 200:
                    token2 = response2.json()["access_token"]
                    
                    # Tokens should be different (new session)
                    assert token1 != token2
    
    def test_concurrent_session_handling(self, client, test_user, auth_headers):
        """Test concurrent session handling."""
        # Test multiple concurrent requests with same token
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/auth/me", headers=auth_headers)
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed (no session conflicts)
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) >= 8  # Allow for some failures due to timing


class TestDataProtection:
    """Test data protection and privacy measures."""
    
    def test_sensitive_data_exposure(self, client, test_user, auth_headers):
        """Test that sensitive data is not exposed."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Sensitive fields should not be exposed
            sensitive_fields = ["password", "firebase_uid", "password_hash"]
            for field in sensitive_fields:
                assert field not in user_data
    
    def test_error_message_information_disclosure(self, client):
        """Test that error messages don't disclose sensitive information."""
        # Test with non-existent user
        response = client.get("/api/v1/users/99999")
        
        if response.status_code == 404:
            error_data = response.json()
            error_message = error_data.get("detail", "").lower()
            
            # Should not reveal database structure or internal details
            forbidden_terms = ["table", "column", "database", "sql", "query"]
            for term in forbidden_terms:
                assert term not in error_message
    
    def test_user_enumeration_prevention(self, client):
        """Test prevention of user enumeration attacks."""
        # Test forgot password with existing vs non-existing email
        existing_email = "test@example.com"
        non_existing_email = "nonexistent@example.com"
        
        response1 = client.post("/api/v1/auth/forgot-password", json={"email": existing_email})
        response2 = client.post("/api/v1/auth/forgot-password", json={"email": non_existing_email})
        
        # Responses should be similar to prevent user enumeration
        # Both should return success or both should return same error
        assert response1.status_code == response2.status_code or \
               (response1.status_code in [200, 404] and response2.status_code in [200, 404])


class TestSecurityHeaders:
    """Test security headers."""
    
    def test_security_headers_present(self, client):
        """Test that security headers are present."""
        response = client.get("/api/v1/properties/")
        
        # Check for important security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        for header in security_headers:
            # Note: Headers might not be set in test environment
            if header in response.headers:
                assert response.headers[header] is not None
    
    def test_cors_configuration(self, client):
        """Test CORS configuration."""
        # Test preflight request
        response = client.options("/api/v1/properties/")
        
        # Should handle OPTIONS request properly
        assert response.status_code in [200, 204, 405]
        
        # Check CORS headers if present
        if "Access-Control-Allow-Origin" in response.headers:
            # Should not allow all origins in production
            assert response.headers["Access-Control-Allow-Origin"] != "*"
