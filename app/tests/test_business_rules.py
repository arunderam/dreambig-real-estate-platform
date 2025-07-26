"""
Unit tests for Business Rules Engine
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.utils.business_rules import (
    BusinessRulesEngine, PropertyValuation, MarketAnalysis, BookingRule,
    PropertyValuationMethod, MarketTrend, RiskLevel
)


class TestPropertyValuation:
    """Test property valuation functionality."""
    
    def test_cma_valuation(self, db_session):
        """Test Comparative Market Analysis valuation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "price": 5000000.0,
            "area": 1200.0,
            "city": "Mumbai",
            "property_type": "apartment",
            "age": 5,
            "amenities": ["parking", "gym"]
        }
        
        valuation = engine.calculate_property_valuation(
            property_data, 
            PropertyValuationMethod.COMPARATIVE_MARKET_ANALYSIS
        )
        
        assert isinstance(valuation, PropertyValuation)
        assert valuation.estimated_value > 0
        assert 0 <= valuation.confidence_score <= 1
        assert valuation.valuation_method == PropertyValuationMethod.COMPARATIVE_MARKET_ANALYSIS
        assert isinstance(valuation.comparable_properties, list)
        assert isinstance(valuation.market_factors, dict)
    
    def test_income_approach_valuation(self, db_session):
        """Test income approach valuation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "expected_rent": 50000.0,
            "area": 1000.0,
            "city": "Mumbai",
            "property_type": "apartment"
        }
        
        valuation = engine.calculate_property_valuation(
            property_data,
            PropertyValuationMethod.INCOME_APPROACH
        )
        
        assert isinstance(valuation, PropertyValuation)
        assert valuation.estimated_value > 0
        assert valuation.valuation_method == PropertyValuationMethod.INCOME_APPROACH
        assert "annual_rent" in valuation.market_factors
        assert "cap_rate" in valuation.market_factors
        assert "net_operating_income" in valuation.market_factors
    
    def test_cost_approach_valuation(self, db_session):
        """Test cost approach valuation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "land_area": 1000.0,
            "built_area": 800.0,
            "city": "Mumbai",
            "property_type": "house",
            "age": 10
        }
        
        valuation = engine.calculate_property_valuation(
            property_data,
            PropertyValuationMethod.COST_APPROACH
        )
        
        assert isinstance(valuation, PropertyValuation)
        assert valuation.estimated_value > 0
        assert valuation.valuation_method == PropertyValuationMethod.COST_APPROACH
        assert "land_value" in valuation.market_factors
        assert "construction_cost" in valuation.market_factors
        assert "depreciation_rate" in valuation.market_factors
    
    def test_avm_valuation(self, db_session):
        """Test Automated Valuation Model."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "price": 5000000.0,
            "area": 1200.0,
            "city": "Mumbai",
            "property_type": "apartment",
            "age": 5,
            "expected_rent": 45000.0
        }
        
        valuation = engine.calculate_property_valuation(
            property_data,
            PropertyValuationMethod.AUTOMATED_VALUATION_MODEL
        )
        
        assert isinstance(valuation, PropertyValuation)
        assert valuation.estimated_value > 0
        assert valuation.valuation_method == PropertyValuationMethod.AUTOMATED_VALUATION_MODEL
        assert "cma_value" in valuation.market_factors
        assert "income_value" in valuation.market_factors
        assert "cost_value" in valuation.market_factors
        assert "weights" in valuation.market_factors
    
    def test_property_adjustments(self, db_session):
        """Test property-specific adjustments."""
        engine = BusinessRulesEngine(db_session)
        
        base_price = 5000.0  # Price per sqft
        
        # Test location premium
        property_data = {
            "location_type": "city_center",
            "age": 3,
            "amenities": ["swimming_pool", "parking"]
        }
        
        adjusted_price = engine._apply_property_adjustments(base_price, property_data)
        
        # Should be higher due to city center location and amenities
        assert adjusted_price > base_price
        
        # Test with less desirable location
        property_data["location_type"] = "outskirts"
        property_data["amenities"] = []
        
        adjusted_price_low = engine._apply_property_adjustments(base_price, property_data)
        
        # Should be lower due to outskirts location
        assert adjusted_price_low < base_price
    
    def test_valuation_error_handling(self, db_session):
        """Test valuation error handling."""
        engine = BusinessRulesEngine(db_session)
        
        # Test with minimal data
        property_data = {}
        
        valuation = engine.calculate_property_valuation(property_data)
        
        # Should return fallback valuation
        assert isinstance(valuation, PropertyValuation)
        assert valuation.confidence_score <= 0.6  # Lower confidence for fallback


class TestMarketAnalysis:
    """Test market analysis functionality."""
    
    def test_analyze_market_trends(self, db_session):
        """Test market trend analysis."""
        engine = BusinessRulesEngine(db_session)
        
        analysis = engine.analyze_market_trends("Mumbai", "apartment")
        
        assert isinstance(analysis, MarketAnalysis)
        assert analysis.area == "Mumbai"
        assert analysis.average_price_per_sqft >= 0
        assert analysis.price_trend in [trend.value for trend in MarketTrend]
        assert analysis.demand_supply_ratio > 0
        assert analysis.risk_assessment in [risk.value for risk in RiskLevel]
        assert isinstance(analysis.market_factors, dict)
    
    def test_price_trend_analysis(self, db_session):
        """Test price trend analysis."""
        engine = BusinessRulesEngine(db_session)
        
        # Mock recent properties with increasing prices
        recent_properties = [
            {
                "price": 4000000,
                "area": 1000,
                "created_at": datetime.utcnow() - timedelta(days=90)
            },
            {
                "price": 4200000,
                "area": 1000,
                "created_at": datetime.utcnow() - timedelta(days=60)
            },
            {
                "price": 4500000,
                "area": 1000,
                "created_at": datetime.utcnow() - timedelta(days=30)
            }
        ]
        
        trend = engine._analyze_price_trend(recent_properties)
        
        # Should detect bullish trend due to increasing prices
        assert trend in [MarketTrend.BULLISH, MarketTrend.STABLE]
    
    def test_risk_assessment(self, db_session):
        """Test market risk assessment."""
        engine = BusinessRulesEngine(db_session)
        
        # Test low risk scenario
        risk = engine._assess_market_risk(
            MarketTrend.STABLE,
            demand_supply_ratio=1.2,
            growth_rate=0.08
        )
        assert risk in [RiskLevel.LOW, RiskLevel.MEDIUM]
        
        # Test high risk scenario
        risk = engine._assess_market_risk(
            MarketTrend.BEARISH,
            demand_supply_ratio=0.5,
            growth_rate=-0.05
        )
        assert risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]


class TestBookingRules:
    """Test booking rules functionality."""
    
    def test_validate_booking_request(self, db_session):
        """Test booking request validation."""
        engine = BusinessRulesEngine(db_session)
        
        booking_data = {
            "preferred_date": datetime.utcnow() + timedelta(days=2),
            "duration_minutes": 60,
            "user_kyc_verified": True
        }
        
        result = engine.validate_booking_request(booking_data)
        
        assert isinstance(result, dict)
        assert "is_valid" in result
        assert "requires_approval" in result
        assert "violations" in result
        assert "recommendations" in result
        assert "pricing_adjustments" in result
        assert isinstance(result["violations"], list)
    
    def test_minimum_advance_booking_rule(self, db_session):
        """Test minimum advance booking rule."""
        engine = BusinessRulesEngine(db_session)
        
        # Booking too soon (less than 24 hours)
        booking_data = {
            "preferred_date": datetime.utcnow() + timedelta(hours=12)
        }
        
        result = engine.validate_booking_request(booking_data)
        
        # Should require approval or be invalid
        assert result["requires_approval"] or not result["is_valid"]
    
    def test_weekend_premium_rule(self, db_session):
        """Test weekend premium rule."""
        engine = BusinessRulesEngine(db_session)
        
        # Get next Saturday
        today = datetime.utcnow()
        days_ahead = 5 - today.weekday()  # Saturday is 5
        if days_ahead <= 0:
            days_ahead += 7
        saturday = today + timedelta(days=days_ahead)
        
        booking_data = {
            "preferred_date": saturday
        }
        
        result = engine.validate_booking_request(booking_data)
        
        # Should have pricing adjustments for weekend
        assert len(result["pricing_adjustments"]) > 0 or len(result["violations"]) > 0
    
    def test_verified_user_priority(self, db_session):
        """Test verified user priority rule."""
        engine = BusinessRulesEngine(db_session)
        
        # Verified user
        booking_data = {
            "preferred_date": datetime.utcnow() + timedelta(days=2),
            "user_kyc_verified": True
        }
        
        result_verified = engine.validate_booking_request(booking_data)
        
        # Unverified user
        booking_data["user_kyc_verified"] = False
        result_unverified = engine.validate_booking_request(booking_data)
        
        # Verified user should have better treatment
        assert result_verified["is_valid"] or not result_unverified["is_valid"]
    
    def test_booking_rule_evaluation(self, db_session):
        """Test individual booking rule evaluation."""
        engine = BusinessRulesEngine(db_session)
        
        rule = BookingRule(
            rule_name="test_rule",
            condition="test_condition",
            action="require_approval",
            priority=1,
            is_active=True
        )
        
        booking_data = {
            "preferred_date": datetime.utcnow() + timedelta(days=1)
        }
        
        result = engine._evaluate_booking_rule(rule, booking_data)
        
        assert isinstance(result, dict)
        assert "violated" in result
        assert "message" in result
        assert "severity" in result


class TestBusinessRulesHelpers:
    """Test business rules helper methods."""
    
    def test_rental_income_estimation(self, db_session):
        """Test rental income estimation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "area": 1000.0,
            "city": "Mumbai"
        }
        
        estimated_rent = engine._estimate_rental_income(property_data)
        
        assert estimated_rent > 0
        assert isinstance(estimated_rent, float)
    
    def test_capitalization_rate(self, db_session):
        """Test capitalization rate calculation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "property_type": "apartment",
            "city": "Mumbai"
        }
        
        cap_rate = engine._get_capitalization_rate(property_data)
        
        assert 0.04 <= cap_rate <= 0.12  # Reasonable cap rate range
        assert isinstance(cap_rate, float)
    
    def test_land_price_estimation(self, db_session):
        """Test land price estimation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {"city": "Mumbai"}
        land_price = engine._get_land_price_per_sqft(property_data)
        
        assert land_price > 0
        assert isinstance(land_price, (int, float))
        
        # Mumbai should be more expensive than smaller cities
        property_data["city"] = "Hyderabad"
        hyderabad_price = engine._get_land_price_per_sqft(property_data)
        
        assert land_price > hyderabad_price
    
    def test_construction_cost_estimation(self, db_session):
        """Test construction cost estimation."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {"property_type": "apartment"}
        cost = engine._get_construction_cost_per_sqft(property_data)
        
        assert cost > 0
        assert isinstance(cost, (int, float))
        
        # Commercial should be more expensive than residential
        property_data["property_type"] = "commercial"
        commercial_cost = engine._get_construction_cost_per_sqft(property_data)
        
        assert commercial_cost > cost
    
    def test_valuation_weights(self, db_session):
        """Test valuation method weights."""
        engine = BusinessRulesEngine(db_session)
        
        # Test for different property types
        property_types = ["apartment", "commercial", "villa"]
        
        for prop_type in property_types:
            property_data = {"property_type": prop_type}
            weights = engine._get_valuation_weights(property_data)
            
            assert isinstance(weights, dict)
            assert "cma" in weights
            assert "income" in weights
            assert "cost" in weights
            
            # Weights should sum to 1.0
            total_weight = sum(weights.values())
            assert abs(total_weight - 1.0) < 0.01
            
            # All weights should be positive
            assert all(weight > 0 for weight in weights.values())


class TestBusinessRulesIntegration:
    """Test business rules integration scenarios."""
    
    def test_complete_property_analysis(self, db_session):
        """Test complete property analysis workflow."""
        engine = BusinessRulesEngine(db_session)
        
        property_data = {
            "price": 5000000.0,
            "area": 1200.0,
            "city": "Mumbai",
            "property_type": "apartment",
            "age": 5,
            "amenities": ["parking", "gym"],
            "expected_rent": 45000.0
        }
        
        # Get valuation
        valuation = engine.calculate_property_valuation(property_data)
        
        # Get market analysis
        market_analysis = engine.analyze_market_trends(
            property_data["city"], 
            property_data["property_type"]
        )
        
        # Validate booking
        booking_data = {
            "preferred_date": datetime.utcnow() + timedelta(days=2),
            "user_kyc_verified": True
        }
        booking_validation = engine.validate_booking_request(booking_data)
        
        # All should return valid results
        assert isinstance(valuation, PropertyValuation)
        assert isinstance(market_analysis, MarketAnalysis)
        assert isinstance(booking_validation, dict)
        assert booking_validation["is_valid"]
    
    def test_error_resilience(self, db_session):
        """Test business rules error resilience."""
        engine = BusinessRulesEngine(db_session)
        
        # Test with empty/invalid data
        empty_data = {}
        
        # Should not raise exceptions
        valuation = engine.calculate_property_valuation(empty_data)
        market_analysis = engine.analyze_market_trends("", "")
        booking_validation = engine.validate_booking_request(empty_data)
        
        # Should return valid objects with fallback values
        assert isinstance(valuation, PropertyValuation)
        assert isinstance(market_analysis, MarketAnalysis)
        assert isinstance(booking_validation, dict)
    
    @patch('app.utils.business_rules.BusinessRulesEngine._get_recent_properties_in_area')
    def test_market_analysis_with_mock_data(self, mock_get_properties, db_session):
        """Test market analysis with mocked property data."""
        # Mock property data
        mock_get_properties.return_value = [
            {
                "price": 5000000,
                "area": 1000,
                "created_at": datetime.utcnow() - timedelta(days=30)
            },
            {
                "price": 5200000,
                "area": 1000,
                "created_at": datetime.utcnow() - timedelta(days=15)
            }
        ]
        
        engine = BusinessRulesEngine(db_session)
        analysis = engine.analyze_market_trends("Mumbai", "apartment")
        
        assert analysis.average_price_per_sqft > 0
        assert analysis.area == "Mumbai"
        mock_get_properties.assert_called_once_with("Mumbai", "apartment")
