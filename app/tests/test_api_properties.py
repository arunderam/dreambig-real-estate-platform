"""
Integration tests for Properties API endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.tests.conftest import assert_response_success, assert_response_error, assert_valid_property_response


class TestPropertiesAPI:
    """Test Properties API endpoints."""
    
    def test_create_property_success(self, client, owner_auth_headers, test_property_data):
        """Test successful property creation."""
        response = client.post(
            "/api/v1/properties/",
            json=test_property_data,
            headers=owner_auth_headers
        )
        
        assert_response_success(response, 201)
        data = response.json()
        assert_valid_property_response(data)
        assert data["title"] == test_property_data["title"]
        assert data["price"] == test_property_data["price"]
    
    def test_create_property_unauthorized(self, client, test_property_data):
        """Test property creation without authentication."""
        response = client.post("/api/v1/properties/", json=test_property_data)
        
        assert_response_error(response, 401)
    
    def test_create_property_invalid_data(self, client, owner_auth_headers):
        """Test property creation with invalid data."""
        invalid_data = {
            "title": "",  # Empty title
            "price": -1000,  # Negative price
            "bhk": 0,  # Invalid BHK
        }
        
        response = client.post(
            "/api/v1/properties/",
            json=invalid_data,
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 422)
    
    def test_get_property_success(self, client, test_property):
        """Test successful property retrieval."""
        response = client.get(f"/api/v1/properties/{test_property.id}")
        
        assert_response_success(response)
        data = response.json()
        assert_valid_property_response(data)
        assert data["id"] == test_property.id
        assert data["title"] == test_property.title
    
    def test_get_property_not_found(self, client):
        """Test getting non-existent property."""
        response = client.get("/api/v1/properties/99999")
        
        assert_response_error(response, 404)
    
    def test_get_properties_list(self, client, integration_test_setup):
        """Test getting list of properties."""
        response = client.get("/api/v1/properties/")
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # From integration_test_setup
        
        for property_data in data:
            assert_valid_property_response(property_data)
    
    def test_get_properties_with_pagination(self, client, integration_test_setup):
        """Test getting properties with pagination."""
        response = client.get("/api/v1/properties/?skip=2&limit=3")
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
    
    def test_update_property_success(self, client, test_property, owner_auth_headers):
        """Test successful property update."""
        update_data = {
            "title": "Updated Property Title",
            "price": 5500000.0,
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/properties/{test_property.id}",
            json=update_data,
            headers=owner_auth_headers
        )
        
        assert_response_success(response)
        data = response.json()
        assert data["title"] == "Updated Property Title"
        assert data["price"] == 5500000.0
        assert data["description"] == "Updated description"
    
    def test_update_property_unauthorized(self, client, test_property):
        """Test property update without authentication."""
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            f"/api/v1/properties/{test_property.id}",
            json=update_data
        )
        
        assert_response_error(response, 401)
    
    def test_update_property_forbidden(self, client, test_property, auth_headers):
        """Test property update by non-owner."""
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            f"/api/v1/properties/{test_property.id}",
            json=update_data,
            headers=auth_headers  # Regular user, not owner
        )
        
        assert_response_error(response, 403)
    
    def test_delete_property_success(self, client, test_property, owner_auth_headers):
        """Test successful property deletion."""
        response = client.delete(
            f"/api/v1/properties/{test_property.id}",
            headers=owner_auth_headers
        )
        
        assert_response_success(response)
        
        # Verify property is deleted
        get_response = client.get(f"/api/v1/properties/{test_property.id}")
        assert_response_error(get_response, 404)
    
    def test_delete_property_unauthorized(self, client, test_property):
        """Test property deletion without authentication."""
        response = client.delete(f"/api/v1/properties/{test_property.id}")
        
        assert_response_error(response, 401)
    
    def test_search_properties_by_city(self, client, integration_test_setup):
        """Test searching properties by city."""
        response = client.get("/api/v1/properties/search?city=Mumbai")
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        
        # All returned properties should be in Mumbai
        for property_data in data:
            assert property_data["city"] == "Mumbai"
    
    def test_search_properties_by_price_range(self, client, integration_test_setup):
        """Test searching properties by price range."""
        response = client.get("/api/v1/properties/search?min_price=1000000&max_price=3000000")
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        
        # All returned properties should be within price range
        for property_data in data:
            assert 1000000 <= property_data["price"] <= 3000000
    
    def test_search_properties_by_bhk(self, client, integration_test_setup):
        """Test searching properties by BHK."""
        response = client.get("/api/v1/properties/search?bhk=3")
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        
        # All returned properties should have 3 BHK
        for property_data in data:
            assert property_data["bhk"] == 3
    
    def test_search_properties_multiple_filters(self, client, integration_test_setup):
        """Test searching properties with multiple filters."""
        response = client.get(
            "/api/v1/properties/search?city=Mumbai&bhk=2&min_price=1500000&max_price=2500000"
        )
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        
        # All returned properties should match all filters
        for property_data in data:
            assert property_data["city"] == "Mumbai"
            assert property_data["bhk"] == 2
            assert 1500000 <= property_data["price"] <= 2500000
    
    def test_get_property_recommendations(self, client, test_user, auth_headers, mock_ai_service):
        """Test getting property recommendations."""
        response = client.get(
            "/api/v1/properties/recommendations",
            headers=auth_headers
        )
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        
        # Verify AI service was called
        mock_ai_service.get_property_recommendations.assert_called_once()
    
    def test_upload_property_image(self, client, test_property, owner_auth_headers, sample_image_file, temp_upload_dir):
        """Test uploading property image."""
        filename, file_content, content_type = sample_image_file
        
        response = client.post(
            f"/api/v1/properties/{test_property.id}/images",
            files={"file": (filename, file_content, content_type)},
            headers=owner_auth_headers
        )
        
        assert_response_success(response, 201)
        data = response.json()
        assert "image_url" in data
        assert "filename" in data
    
    def test_upload_property_video(self, client, test_property, owner_auth_headers, sample_video_file, temp_upload_dir):
        """Test uploading property video."""
        filename, file_content, content_type = sample_video_file
        
        response = client.post(
            f"/api/v1/properties/{test_property.id}/videos",
            files={"file": (filename, file_content, content_type)},
            headers=owner_auth_headers
        )
        
        assert_response_success(response, 201)
        data = response.json()
        assert "video_url" in data
        assert "filename" in data
    
    def test_upload_invalid_file_type(self, client, test_property, owner_auth_headers):
        """Test uploading invalid file type."""
        import io
        
        # Create a text file (invalid for images)
        text_content = io.BytesIO(b"This is not an image")
        
        response = client.post(
            f"/api/v1/properties/{test_property.id}/images",
            files={"file": ("test.txt", text_content, "text/plain")},
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 400)
    
    def test_get_property_analytics(self, client, test_property, owner_auth_headers):
        """Test getting property analytics."""
        response = client.get(
            f"/api/v1/properties/{test_property.id}/analytics",
            headers=owner_auth_headers
        )
        
        assert_response_success(response)
        data = response.json()
        assert "views" in data
        assert "inquiries" in data
        assert "bookings" in data
        assert isinstance(data["views"], int)
    
    def test_property_comparison(self, client, integration_test_setup):
        """Test property comparison feature."""
        properties = integration_test_setup["properties"]
        property_ids = [properties[0].id, properties[1].id, properties[2].id]
        
        response = client.post(
            "/api/v1/properties/compare",
            json={"property_ids": property_ids}
        )
        
        assert_response_success(response)
        data = response.json()
        assert "properties" in data
        assert "comparison" in data
        assert len(data["properties"]) == 3
    
    def test_get_similar_properties(self, client, test_property, mock_ai_service):
        """Test getting similar properties."""
        response = client.get(f"/api/v1/properties/{test_property.id}/similar")
        
        assert_response_success(response)
        data = response.json()
        assert isinstance(data, list)
        
        # Verify AI service was called
        mock_ai_service.get_property_recommendations.assert_called_once()
    
    def test_property_valuation(self, client, test_property, mock_business_rules):
        """Test property valuation."""
        response = client.get(f"/api/v1/properties/{test_property.id}/valuation")
        
        assert_response_success(response)
        data = response.json()
        assert "estimated_value" in data
        assert "confidence_score" in data
        assert "valuation_method" in data
        assert isinstance(data["estimated_value"], (int, float))
        assert 0 <= data["confidence_score"] <= 1
    
    def test_property_market_analysis(self, client, test_property, mock_business_rules):
        """Test property market analysis."""
        response = client.get(f"/api/v1/properties/{test_property.id}/market-analysis")
        
        assert_response_success(response)
        data = response.json()
        assert "area" in data
        assert "average_price_per_sqft" in data
        assert "price_trend" in data
        assert "risk_assessment" in data


class TestPropertiesAPIValidation:
    """Test Properties API input validation."""
    
    def test_create_property_missing_required_fields(self, client, owner_auth_headers):
        """Test property creation with missing required fields."""
        incomplete_data = {
            "title": "Test Property"
            # Missing price, bhk, area, etc.
        }
        
        response = client.post(
            "/api/v1/properties/",
            json=incomplete_data,
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 422)
        error_data = response.json()
        assert "detail" in error_data
    
    def test_create_property_invalid_price(self, client, owner_auth_headers, test_property_data):
        """Test property creation with invalid price."""
        invalid_data = test_property_data.copy()
        invalid_data["price"] = -1000  # Negative price
        
        response = client.post(
            "/api/v1/properties/",
            json=invalid_data,
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 422)
    
    def test_create_property_invalid_bhk(self, client, owner_auth_headers, test_property_data):
        """Test property creation with invalid BHK."""
        invalid_data = test_property_data.copy()
        invalid_data["bhk"] = 0  # Invalid BHK
        
        response = client.post(
            "/api/v1/properties/",
            json=invalid_data,
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 422)
    
    def test_create_property_invalid_area(self, client, owner_auth_headers, test_property_data):
        """Test property creation with invalid area."""
        invalid_data = test_property_data.copy()
        invalid_data["area"] = -500  # Negative area
        
        response = client.post(
            "/api/v1/properties/",
            json=invalid_data,
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 422)
    
    def test_create_property_invalid_property_type(self, client, owner_auth_headers, test_property_data):
        """Test property creation with invalid property type."""
        invalid_data = test_property_data.copy()
        invalid_data["property_type"] = "invalid_type"
        
        response = client.post(
            "/api/v1/properties/",
            json=invalid_data,
            headers=owner_auth_headers
        )
        
        assert_response_error(response, 422)
    
    def test_search_properties_invalid_parameters(self, client):
        """Test property search with invalid parameters."""
        # Invalid price range
        response = client.get("/api/v1/properties/search?min_price=5000000&max_price=1000000")
        
        assert_response_error(response, 400)
        error_data = response.json()
        assert "min_price cannot be greater than max_price" in error_data["detail"]
    
    def test_search_properties_invalid_bhk(self, client):
        """Test property search with invalid BHK."""
        response = client.get("/api/v1/properties/search?bhk=0")
        
        assert_response_error(response, 422)
    
    def test_property_comparison_too_many_properties(self, client):
        """Test property comparison with too many properties."""
        property_ids = list(range(1, 11))  # 10 properties (assuming max is 5)
        
        response = client.post(
            "/api/v1/properties/compare",
            json={"property_ids": property_ids}
        )
        
        assert_response_error(response, 400)
        error_data = response.json()
        assert "too many properties" in error_data["detail"].lower()
    
    def test_property_comparison_duplicate_ids(self, client):
        """Test property comparison with duplicate property IDs."""
        property_ids = [1, 2, 2, 3]  # Duplicate ID
        
        response = client.post(
            "/api/v1/properties/compare",
            json={"property_ids": property_ids}
        )
        
        assert_response_error(response, 400)
        error_data = response.json()
        assert "duplicate" in error_data["detail"].lower()
