"""
Integration tests for Authentication API endpoints
"""
import pytest
import json
from unittest.mock import patch, Mock

from app.tests.conftest import assert_response_success, assert_response_error, assert_valid_user_response


class TestAuthAPI:
    """Test Authentication API endpoints."""
    
    def test_register_user_success(self, client, mock_firebase):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "phone": "+1234567890",
            "role": "tenant",
            "preferences": {
                "budget_min": 1000000,
                "budget_max": 5000000,
                "preferred_locations": ["Mumbai", "Delhi"]
            }
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert_response_success(response, 201)
        data = response.json()
        assert_valid_user_response(data["user"])
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["name"] == user_data["name"]
        assert "access_token" in data
        assert "token_type" in data
    
    def test_register_user_duplicate_email(self, client, test_user, mock_firebase):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,  # Existing email
            "name": "Another User",
            "phone": "+9876543210",
            "role": "tenant"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert_response_error(response, 400)
        error_data = response.json()
        assert "already registered" in error_data["detail"].lower()
    
    def test_register_user_invalid_email(self, client, mock_firebase):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",  # Invalid email format
            "name": "Test User",
            "phone": "+1234567890",
            "role": "tenant"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert_response_error(response, 422)
    
    def test_register_user_invalid_role(self, client, mock_firebase):
        """Test registration with invalid role."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "+1234567890",
            "role": "invalid_role"  # Invalid role
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert_response_error(response, 422)
    
    def test_login_success(self, client, test_user, mock_firebase):
        """Test successful login."""
        # Mock Firebase token verification
        mock_firebase.return_value = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.name
        }
        
        login_data = {
            "firebase_token": "valid_firebase_token"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert_response_success(response)
        data = response.json()
        assert_valid_user_response(data["user"])
        assert data["user"]["id"] == test_user.id
        assert "access_token" in data
        assert "token_type" in data
    
    def test_login_invalid_token(self, client):
        """Test login with invalid Firebase token."""
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            login_data = {
                "firebase_token": "invalid_firebase_token"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert_response_error(response, 401)
    
    def test_login_user_not_found(self, client):
        """Test login with valid token but user not in database."""
        with patch('app.core.security.verify_firebase_token') as mock_verify:
            mock_verify.return_value = {
                "uid": "nonexistent_firebase_uid",
                "email": "nonexistent@example.com",
                "name": "Nonexistent User"
            }
            
            login_data = {
                "firebase_token": "valid_firebase_token"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert_response_error(response, 404)
    
    def test_get_current_user(self, client, test_user, auth_headers):
        """Test getting current user information."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert_response_success(response)
        data = response.json()
        assert_valid_user_response(data)
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert_response_error(response, 401)
    
    def test_update_user_profile(self, client, test_user, auth_headers):
        """Test updating user profile."""
        update_data = {
            "name": "Updated Name",
            "phone": "+9876543210",
            "preferences": {
                "budget_min": 2000000,
                "budget_max": 8000000,
                "preferred_locations": ["Bangalore", "Chennai"]
            }
        }
        
        response = client.put(
            "/api/v1/auth/profile",
            json=update_data,
            headers=auth_headers
        )
        
        assert_response_success(response)
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "+9876543210"
    
    def test_update_user_profile_unauthorized(self, client):
        """Test updating profile without authentication."""
        update_data = {"name": "Updated Name"}
        
        response = client.put("/api/v1/auth/profile", json=update_data)
        
        assert_response_error(response, 401)
    
    def test_refresh_token(self, client, test_user, auth_headers):
        """Test token refresh."""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert_response_success(response)
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client, test_user, auth_headers):
        """Test user logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert_response_success(response)
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    def test_change_password(self, client, test_user, auth_headers, mock_firebase):
        """Test password change."""
        password_data = {
            "current_password": "current_password",
            "new_password": "new_password123",
            "confirm_password": "new_password123"
        }
        
        with patch('app.core.security.change_firebase_password') as mock_change:
            mock_change.return_value = True
            
            response = client.post(
                "/api/v1/auth/change-password",
                json=password_data,
                headers=auth_headers
            )
            
            assert_response_success(response)
            data = response.json()
            assert data["message"] == "Password changed successfully"
    
    def test_change_password_mismatch(self, client, test_user, auth_headers):
        """Test password change with mismatched passwords."""
        password_data = {
            "current_password": "current_password",
            "new_password": "new_password123",
            "confirm_password": "different_password"  # Mismatch
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 400)
        error_data = response.json()
        assert "passwords do not match" in error_data["detail"].lower()
    
    def test_forgot_password(self, client, test_user, mock_email_service):
        """Test forgot password functionality."""
        forgot_data = {
            "email": test_user.email
        }
        
        with patch('app.core.security.send_password_reset_email') as mock_send:
            mock_send.return_value = True
            
            response = client.post("/api/v1/auth/forgot-password", json=forgot_data)
            
            assert_response_success(response)
            data = response.json()
            assert "reset link sent" in data["message"].lower()
    
    def test_forgot_password_invalid_email(self, client):
        """Test forgot password with invalid email."""
        forgot_data = {
            "email": "nonexistent@example.com"
        }
        
        response = client.post("/api/v1/auth/forgot-password", json=forgot_data)
        
        assert_response_error(response, 404)
    
    def test_reset_password(self, client, test_user):
        """Test password reset with valid token."""
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "new_password123",
            "confirm_password": "new_password123"
        }
        
        with patch('app.core.security.verify_password_reset_token') as mock_verify:
            mock_verify.return_value = test_user.firebase_uid
            
            with patch('app.core.security.reset_firebase_password') as mock_reset:
                mock_reset.return_value = True
                
                response = client.post("/api/v1/auth/reset-password", json=reset_data)
                
                assert_response_success(response)
                data = response.json()
                assert "password reset successfully" in data["message"].lower()
    
    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_reset_token",
            "new_password": "new_password123",
            "confirm_password": "new_password123"
        }
        
        with patch('app.core.security.verify_password_reset_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            response = client.post("/api/v1/auth/reset-password", json=reset_data)
            
            assert_response_error(response, 400)
    
    def test_verify_email(self, client, test_user):
        """Test email verification."""
        verify_data = {
            "token": "valid_verification_token"
        }
        
        with patch('app.core.security.verify_email_token') as mock_verify:
            mock_verify.return_value = test_user.firebase_uid
            
            response = client.post("/api/v1/auth/verify-email", json=verify_data)
            
            assert_response_success(response)
            data = response.json()
            assert "email verified successfully" in data["message"].lower()
    
    def test_resend_verification_email(self, client, test_user, auth_headers, mock_email_service):
        """Test resending verification email."""
        with patch('app.core.security.send_verification_email') as mock_send:
            mock_send.return_value = True
            
            response = client.post(
                "/api/v1/auth/resend-verification",
                headers=auth_headers
            )
            
            assert_response_success(response)
            data = response.json()
            assert "verification email sent" in data["message"].lower()


class TestAuthAPIValidation:
    """Test Authentication API input validation."""
    
    def test_register_missing_required_fields(self, client, mock_firebase):
        """Test registration with missing required fields."""
        incomplete_data = {
            "email": "test@example.com"
            # Missing name, phone, role
        }
        
        response = client.post("/api/v1/auth/register", json=incomplete_data)
        
        assert_response_error(response, 422)
    
    def test_register_invalid_phone_format(self, client, mock_firebase):
        """Test registration with invalid phone format."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "phone": "invalid_phone",  # Invalid format
            "role": "tenant"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert_response_error(response, 422)
    
    def test_login_missing_token(self, client):
        """Test login without Firebase token."""
        response = client.post("/api/v1/auth/login", json={})
        
        assert_response_error(response, 422)
    
    def test_change_password_weak_password(self, client, test_user, auth_headers):
        """Test password change with weak password."""
        password_data = {
            "current_password": "current_password",
            "new_password": "123",  # Too weak
            "confirm_password": "123"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 422)
    
    def test_update_profile_invalid_preferences(self, client, test_user, auth_headers):
        """Test profile update with invalid preferences."""
        update_data = {
            "preferences": {
                "budget_min": 5000000,
                "budget_max": 1000000  # Min > Max (invalid)
            }
        }
        
        response = client.put(
            "/api/v1/auth/profile",
            json=update_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 400)


class TestAuthAPIPermissions:
    """Test Authentication API permissions and roles."""
    
    def test_admin_only_endpoint_success(self, client, test_admin_user, admin_auth_headers):
        """Test admin-only endpoint with admin user."""
        response = client.get("/api/v1/auth/admin/users", headers=admin_auth_headers)
        
        assert_response_success(response)
    
    def test_admin_only_endpoint_forbidden(self, client, test_user, auth_headers):
        """Test admin-only endpoint with regular user."""
        response = client.get("/api/v1/auth/admin/users", headers=auth_headers)
        
        assert_response_error(response, 403)
    
    def test_owner_permissions(self, client, test_property_owner, owner_auth_headers):
        """Test owner-specific permissions."""
        response = client.get("/api/v1/auth/owner/dashboard", headers=owner_auth_headers)
        
        assert_response_success(response)
    
    def test_role_based_access_control(self, client, test_user, auth_headers):
        """Test role-based access control."""
        # Regular tenant trying to access owner endpoint
        response = client.get("/api/v1/auth/owner/dashboard", headers=auth_headers)
        
        assert_response_error(response, 403)
