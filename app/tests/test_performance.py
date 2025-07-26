"""
Performance tests for DreamBig Real Estate Platform
"""
import pytest
import time
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics

from app.db import crud
from app.db.crud_bookings import create_property_booking
from app.utils.business_rules import BusinessRulesEngine
from app.core.advanced_search import search_properties


class TestDatabasePerformance:
    """Test database operation performance."""
    
    def test_user_creation_performance(self, db_session, performance_test_data):
        """Test user creation performance."""
        users_count = performance_test_data["users_count"]
        
        start_time = time.time()
        
        for i in range(users_count):
            user_data = {
                "email": f"perftest_user_{i}@example.com",
                "name": f"Performance Test User {i}",
                "phone": f"+123456789{i:02d}",
                "firebase_uid": f"perf_test_uid_{i}",
                "role": "tenant"
            }
            crud.create_user(db_session, user_data)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert total_time < 30.0  # Should complete within 30 seconds
        avg_time_per_user = total_time / users_count
        assert avg_time_per_user < 0.3  # Less than 300ms per user
        
        print(f"Created {users_count} users in {total_time:.2f}s (avg: {avg_time_per_user:.3f}s per user)")
    
    def test_property_creation_performance(self, db_session, test_property_owner, performance_test_data):
        """Test property creation performance."""
        properties_count = performance_test_data["properties_count"]
        
        start_time = time.time()
        
        for i in range(properties_count):
            property_data = {
                "title": f"Performance Test Property {i}",
                "description": f"Description for performance test property {i}",
                "price": 1000000.0 + (i * 100000),
                "bhk": (i % 4) + 1,
                "area": 800.0 + (i * 50),
                "property_type": ["apartment", "house", "villa"][i % 3],
                "furnishing": ["furnished", "semi_furnished", "unfurnished"][i % 3],
                "address": f"{i+1} Performance Test Street",
                "city": ["Mumbai", "Delhi", "Bangalore"][i % 3],
                "state": ["Maharashtra", "Delhi", "Karnataka"][i % 3],
                "pincode": f"40000{i % 10}",
                "latitude": 19.0760 + (i * 0.001),
                "longitude": 72.8777 + (i * 0.001),
                "owner_id": test_property_owner.id
            }
            crud.create_property(db_session, property_data)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert total_time < 60.0  # Should complete within 60 seconds
        avg_time_per_property = total_time / properties_count
        assert avg_time_per_property < 0.5  # Less than 500ms per property
        
        print(f"Created {properties_count} properties in {total_time:.2f}s (avg: {avg_time_per_property:.3f}s per property)")
    
    def test_property_search_performance(self, db_session, integration_test_setup):
        """Test property search performance."""
        search_iterations = 100
        search_times = []
        
        for i in range(search_iterations):
            start_time = time.time()
            
            # Perform different types of searches
            if i % 4 == 0:
                results = crud.search_properties(db_session, city="Mumbai")
            elif i % 4 == 1:
                results = crud.search_properties(db_session, min_price=1000000, max_price=5000000)
            elif i % 4 == 2:
                results = crud.search_properties(db_session, bhk=3)
            else:
                results = crud.search_properties(db_session, property_type="apartment")
            
            end_time = time.time()
            search_time = end_time - start_time
            search_times.append(search_time)
        
        # Performance analysis
        avg_search_time = statistics.mean(search_times)
        max_search_time = max(search_times)
        min_search_time = min(search_times)
        
        # Performance assertions
        assert avg_search_time < 0.1  # Average search should be under 100ms
        assert max_search_time < 0.5   # No search should take more than 500ms
        assert min_search_time < 0.05  # Fastest search should be under 50ms
        
        print(f"Search performance - Avg: {avg_search_time:.3f}s, Max: {max_search_time:.3f}s, Min: {min_search_time:.3f}s")
    
    def test_booking_creation_performance(self, db_session, test_user, test_property, performance_test_data):
        """Test booking creation performance."""
        bookings_count = performance_test_data["bookings_count"]
        
        start_time = time.time()
        
        for i in range(bookings_count):
            booking_data = {
                "booking_type": "viewing",
                "property_id": test_property.id,
                "user_id": test_user.id,
                "preferred_date": datetime.utcnow() + timedelta(days=i+1),
                "preferred_time": f"{10 + (i % 8)}:00",
                "duration_minutes": 60,
                "contact_name": f"Test User {i}",
                "contact_phone": f"+123456789{i:02d}",
                "contact_email": f"test{i}@example.com"
            }
            create_property_booking(db_session, booking_data)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert total_time < 30.0  # Should complete within 30 seconds
        avg_time_per_booking = total_time / bookings_count
        assert avg_time_per_booking < 0.15  # Less than 150ms per booking
        
        print(f"Created {bookings_count} bookings in {total_time:.2f}s (avg: {avg_time_per_booking:.3f}s per booking)")


class TestAPIPerformance:
    """Test API endpoint performance."""
    
    def test_property_list_api_performance(self, client, integration_test_setup):
        """Test property list API performance."""
        iterations = 50
        response_times = []
        
        for i in range(iterations):
            start_time = time.time()
            response = client.get("/api/v1/properties/")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            response_times.append(response_time)
        
        # Performance analysis
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        
        # Performance assertions
        assert avg_response_time < 0.2   # Average response under 200ms
        assert max_response_time < 1.0   # No response over 1 second
        assert p95_response_time < 0.5   # 95th percentile under 500ms
        
        print(f"Property list API - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s, P95: {p95_response_time:.3f}s")
    
    def test_property_search_api_performance(self, client, integration_test_setup):
        """Test property search API performance."""
        search_queries = [
            "?city=Mumbai",
            "?min_price=1000000&max_price=5000000",
            "?bhk=3",
            "?property_type=apartment",
            "?city=Mumbai&bhk=2&min_price=2000000"
        ]
        
        response_times = []
        
        for query in search_queries:
            for _ in range(10):  # 10 iterations per query
                start_time = time.time()
                response = client.get(f"/api/v1/properties/search{query}")
                end_time = time.time()
                
                assert response.status_code == 200
                response_time = end_time - start_time
                response_times.append(response_time)
        
        # Performance analysis
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Performance assertions
        assert avg_response_time < 0.3   # Average search under 300ms
        assert max_response_time < 1.0   # No search over 1 second
        
        print(f"Property search API - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")
    
    def test_user_authentication_performance(self, client, test_user, mock_firebase):
        """Test user authentication performance."""
        iterations = 100
        response_times = []
        
        for i in range(iterations):
            login_data = {"firebase_token": f"test_token_{i}"}
            
            start_time = time.time()
            response = client.post("/api/v1/auth/login", json=login_data)
            end_time = time.time()
            
            # Note: This will fail authentication, but we're testing response time
            response_time = end_time - start_time
            response_times.append(response_time)
        
        # Performance analysis
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Performance assertions
        assert avg_response_time < 0.1   # Average auth under 100ms
        assert max_response_time < 0.5   # No auth over 500ms
        
        print(f"Authentication API - Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s")


class TestConcurrentPerformance:
    """Test concurrent operation performance."""
    
    def test_concurrent_property_creation(self, db_session, test_property_owner):
        """Test concurrent property creation."""
        concurrent_requests = 10
        properties_per_request = 20
        
        def create_properties_batch(batch_id: int) -> float:
            """Create a batch of properties and return time taken."""
            start_time = time.time()
            
            for i in range(properties_per_request):
                property_data = {
                    "title": f"Concurrent Property {batch_id}_{i}",
                    "price": 1000000.0 + (i * 50000),
                    "bhk": (i % 3) + 1,
                    "area": 800.0 + (i * 25),
                    "property_type": "apartment",
                    "city": "Mumbai",
                    "owner_id": test_property_owner.id
                }
                crud.create_property(db_session, property_data)
            
            return time.time() - start_time
        
        # Execute concurrent property creation
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(create_properties_batch, i) 
                for i in range(concurrent_requests)
            ]
            batch_times = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        total_properties = concurrent_requests * properties_per_request
        
        # Performance assertions
        assert total_time < 60.0  # Should complete within 60 seconds
        avg_batch_time = statistics.mean(batch_times)
        assert avg_batch_time < 30.0  # Each batch should complete within 30 seconds
        
        print(f"Created {total_properties} properties concurrently in {total_time:.2f}s")
        print(f"Average batch time: {avg_batch_time:.2f}s")
    
    def test_concurrent_api_requests(self, client, integration_test_setup):
        """Test concurrent API requests."""
        concurrent_requests = 20
        
        def make_api_request(request_id: int) -> Dict[str, Any]:
            """Make an API request and return timing info."""
            start_time = time.time()
            
            # Alternate between different endpoints
            if request_id % 3 == 0:
                response = client.get("/api/v1/properties/")
            elif request_id % 3 == 1:
                response = client.get("/api/v1/properties/search?city=Mumbai")
            else:
                properties = integration_test_setup["properties"]
                if properties:
                    response = client.get(f"/api/v1/properties/{properties[0].id}")
                else:
                    response = client.get("/api/v1/properties/")
            
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }
        
        # Execute concurrent API requests
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(make_api_request, i) 
                for i in range(concurrent_requests)
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r["status_code"] == 200]
        response_times = [r["response_time"] for r in successful_requests]
        
        # Performance assertions
        assert len(successful_requests) >= concurrent_requests * 0.95  # 95% success rate
        assert total_time < 10.0  # All requests should complete within 10 seconds
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 1.0   # Average response under 1 second
            assert max_response_time < 3.0   # No response over 3 seconds
            
            print(f"Concurrent API test - {len(successful_requests)}/{concurrent_requests} successful")
            print(f"Total time: {total_time:.2f}s, Avg response: {avg_response_time:.3f}s")


class TestBusinessRulesPerformance:
    """Test business rules engine performance."""
    
    def test_property_valuation_performance(self, db_session):
        """Test property valuation performance."""
        engine = BusinessRulesEngine(db_session)
        iterations = 100
        valuation_times = []
        
        property_data = {
            "price": 5000000.0,
            "area": 1200.0,
            "city": "Mumbai",
            "property_type": "apartment",
            "age": 5,
            "amenities": ["parking", "gym"]
        }
        
        for i in range(iterations):
            start_time = time.time()
            valuation = engine.calculate_property_valuation(property_data)
            end_time = time.time()
            
            valuation_time = end_time - start_time
            valuation_times.append(valuation_time)
            
            # Verify valuation is valid
            assert valuation.estimated_value > 0
        
        # Performance analysis
        avg_valuation_time = statistics.mean(valuation_times)
        max_valuation_time = max(valuation_times)
        
        # Performance assertions
        assert avg_valuation_time < 0.05  # Average valuation under 50ms
        assert max_valuation_time < 0.2   # No valuation over 200ms
        
        print(f"Property valuation - Avg: {avg_valuation_time:.3f}s, Max: {max_valuation_time:.3f}s")
    
    def test_market_analysis_performance(self, db_session):
        """Test market analysis performance."""
        engine = BusinessRulesEngine(db_session)
        iterations = 50
        analysis_times = []
        
        for i in range(iterations):
            start_time = time.time()
            analysis = engine.analyze_market_trends("Mumbai", "apartment")
            end_time = time.time()
            
            analysis_time = end_time - start_time
            analysis_times.append(analysis_time)
            
            # Verify analysis is valid
            assert analysis.area == "Mumbai"
        
        # Performance analysis
        avg_analysis_time = statistics.mean(analysis_times)
        max_analysis_time = max(analysis_times)
        
        # Performance assertions
        assert avg_analysis_time < 0.1   # Average analysis under 100ms
        assert max_analysis_time < 0.5   # No analysis over 500ms
        
        print(f"Market analysis - Avg: {avg_analysis_time:.3f}s, Max: {max_analysis_time:.3f}s")
    
    def test_booking_validation_performance(self, db_session):
        """Test booking validation performance."""
        engine = BusinessRulesEngine(db_session)
        iterations = 200
        validation_times = []
        
        booking_data = {
            "preferred_date": datetime.utcnow() + timedelta(days=2),
            "duration_minutes": 60,
            "user_kyc_verified": True
        }
        
        for i in range(iterations):
            start_time = time.time()
            result = engine.validate_booking_request(booking_data)
            end_time = time.time()
            
            validation_time = end_time - start_time
            validation_times.append(validation_time)
            
            # Verify validation result is valid
            assert isinstance(result, dict)
            assert "is_valid" in result
        
        # Performance analysis
        avg_validation_time = statistics.mean(validation_times)
        max_validation_time = max(validation_times)
        
        # Performance assertions
        assert avg_validation_time < 0.01  # Average validation under 10ms
        assert max_validation_time < 0.05  # No validation over 50ms
        
        print(f"Booking validation - Avg: {avg_validation_time:.3f}s, Max: {max_validation_time:.3f}s")


class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    def test_large_dataset_handling(self, db_session, test_property_owner):
        """Test handling of large datasets."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a large number of properties
        large_dataset_size = 1000
        
        for i in range(large_dataset_size):
            property_data = {
                "title": f"Large Dataset Property {i}",
                "price": 1000000.0 + (i * 10000),
                "bhk": (i % 4) + 1,
                "area": 800.0 + (i * 10),
                "property_type": "apartment",
                "city": "Mumbai",
                "owner_id": test_property_owner.id
            }
            crud.create_property(db_session, property_data)
        
        # Test querying large dataset
        start_time = time.time()
        properties = crud.get_properties(db_session, skip=0, limit=1000)
        query_time = time.time() - start_time
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Performance assertions
        assert len(properties) == large_dataset_size
        assert query_time < 2.0  # Query should complete within 2 seconds
        assert memory_increase < 500  # Memory increase should be less than 500MB
        
        print(f"Large dataset test - Query time: {query_time:.2f}s, Memory increase: {memory_increase:.1f}MB")
