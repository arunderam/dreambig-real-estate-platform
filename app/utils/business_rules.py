"""
Business Rules Engine for DreamBig Real Estate Platform
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

class PropertyValuationMethod(str, Enum):
    COMPARATIVE_MARKET_ANALYSIS = "cma"
    INCOME_APPROACH = "income"
    COST_APPROACH = "cost"
    AUTOMATED_VALUATION_MODEL = "avm"

class MarketTrend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    STABLE = "stable"
    VOLATILE = "volatile"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class PropertyValuation:
    estimated_value: float
    confidence_score: float
    valuation_method: PropertyValuationMethod
    comparable_properties: List[Dict[str, Any]]
    market_factors: Dict[str, Any]
    last_updated: datetime

@dataclass
class MarketAnalysis:
    area: str
    average_price_per_sqft: float
    price_trend: MarketTrend
    demand_supply_ratio: float
    growth_rate: float
    risk_assessment: RiskLevel
    market_factors: Dict[str, Any]

@dataclass
class BookingRule:
    rule_name: str
    condition: str
    action: str
    priority: int
    is_active: bool

class BusinessRulesEngine:
    """Advanced business logic engine for real estate operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.booking_rules = self._load_booking_rules()
        self.pricing_factors = self._load_pricing_factors()
    
    def _load_booking_rules(self) -> List[BookingRule]:
        """Load booking business rules"""
        return [
            BookingRule(
                rule_name="prevent_double_booking",
                condition="same_property_same_time",
                action="reject_booking",
                priority=1,
                is_active=True
            ),
            BookingRule(
                rule_name="minimum_advance_booking",
                condition="booking_time < 24_hours",
                action="require_approval",
                priority=2,
                is_active=True
            ),
            BookingRule(
                rule_name="maximum_booking_duration",
                condition="duration > 3_hours",
                action="require_approval",
                priority=3,
                is_active=True
            ),
            BookingRule(
                rule_name="weekend_premium",
                condition="weekend_booking",
                action="apply_premium",
                priority=4,
                is_active=True
            ),
            BookingRule(
                rule_name="verified_user_priority",
                condition="user_kyc_verified",
                action="priority_booking",
                priority=5,
                is_active=True
            )
        ]
    
    def _load_pricing_factors(self) -> Dict[str, float]:
        """Load pricing factors for property valuation"""
        return {
            "location_premium": {
                "city_center": 1.3,
                "business_district": 1.25,
                "residential_area": 1.0,
                "suburban": 0.85,
                "outskirts": 0.7
            },
            "property_age": {
                "new_construction": 1.2,
                "0_5_years": 1.1,
                "5_10_years": 1.0,
                "10_20_years": 0.9,
                "20_plus_years": 0.8
            },
            "amenities": {
                "swimming_pool": 0.05,
                "gym": 0.03,
                "parking": 0.08,
                "security": 0.04,
                "elevator": 0.06,
                "garden": 0.04,
                "balcony": 0.03
            },
            "market_conditions": {
                "high_demand": 1.15,
                "normal_demand": 1.0,
                "low_demand": 0.9,
                "recession": 0.8
            }
        }
    
    # Property Valuation Methods
    
    def calculate_property_valuation(
        self, 
        property_data: Dict[str, Any],
        method: PropertyValuationMethod = PropertyValuationMethod.COMPARATIVE_MARKET_ANALYSIS
    ) -> PropertyValuation:
        """Calculate property valuation using specified method"""
        try:
            if method == PropertyValuationMethod.COMPARATIVE_MARKET_ANALYSIS:
                return self._cma_valuation(property_data)
            elif method == PropertyValuationMethod.INCOME_APPROACH:
                return self._income_approach_valuation(property_data)
            elif method == PropertyValuationMethod.COST_APPROACH:
                return self._cost_approach_valuation(property_data)
            elif method == PropertyValuationMethod.AUTOMATED_VALUATION_MODEL:
                return self._avm_valuation(property_data)
            else:
                raise ValueError(f"Unsupported valuation method: {method}")
                
        except Exception as e:
            logger.error(f"Error calculating property valuation: {str(e)}")
            # Return fallback valuation
            return PropertyValuation(
                estimated_value=property_data.get("price", 0),
                confidence_score=0.5,
                valuation_method=method,
                comparable_properties=[],
                market_factors={},
                last_updated=datetime.utcnow()
            )
    
    def _cma_valuation(self, property_data: Dict[str, Any]) -> PropertyValuation:
        """Comparative Market Analysis valuation"""
        # Find comparable properties
        comparable_properties = self._find_comparable_properties(property_data)
        
        if not comparable_properties:
            # Fallback to basic calculation
            base_price = property_data.get("price", 0)
            return PropertyValuation(
                estimated_value=base_price,
                confidence_score=0.6,
                valuation_method=PropertyValuationMethod.COMPARATIVE_MARKET_ANALYSIS,
                comparable_properties=[],
                market_factors={"note": "No comparable properties found"},
                last_updated=datetime.utcnow()
            )
        
        # Calculate average price per sqft from comparables
        total_price_per_sqft = sum(
            comp["price"] / comp["area"] for comp in comparable_properties
        )
        avg_price_per_sqft = total_price_per_sqft / len(comparable_properties)
        
        # Apply adjustments
        adjusted_price_per_sqft = self._apply_property_adjustments(
            avg_price_per_sqft, property_data
        )
        
        # Calculate estimated value
        estimated_value = adjusted_price_per_sqft * property_data.get("area", 0)
        
        # Calculate confidence score based on number of comparables and recency
        confidence_score = min(0.9, 0.5 + (len(comparable_properties) * 0.1))
        
        return PropertyValuation(
            estimated_value=estimated_value,
            confidence_score=confidence_score,
            valuation_method=PropertyValuationMethod.COMPARATIVE_MARKET_ANALYSIS,
            comparable_properties=comparable_properties,
            market_factors={
                "avg_price_per_sqft": avg_price_per_sqft,
                "adjusted_price_per_sqft": adjusted_price_per_sqft,
                "comparables_count": len(comparable_properties)
            },
            last_updated=datetime.utcnow()
        )
    
    def _income_approach_valuation(self, property_data: Dict[str, Any]) -> PropertyValuation:
        """Income approach valuation (for rental properties)"""
        monthly_rent = property_data.get("expected_rent", 0)
        if not monthly_rent:
            # Estimate rent based on area and location
            monthly_rent = self._estimate_rental_income(property_data)
        
        annual_rent = monthly_rent * 12
        
        # Apply vacancy and expense factors
        vacancy_rate = 0.05  # 5% vacancy
        expense_ratio = 0.3   # 30% for maintenance, taxes, etc.
        
        net_operating_income = annual_rent * (1 - vacancy_rate - expense_ratio)
        
        # Capitalization rate based on location and property type
        cap_rate = self._get_capitalization_rate(property_data)
        
        estimated_value = net_operating_income / cap_rate
        
        return PropertyValuation(
            estimated_value=estimated_value,
            confidence_score=0.75,
            valuation_method=PropertyValuationMethod.INCOME_APPROACH,
            comparable_properties=[],
            market_factors={
                "annual_rent": annual_rent,
                "net_operating_income": net_operating_income,
                "cap_rate": cap_rate,
                "vacancy_rate": vacancy_rate,
                "expense_ratio": expense_ratio
            },
            last_updated=datetime.utcnow()
        )
    
    def _cost_approach_valuation(self, property_data: Dict[str, Any]) -> PropertyValuation:
        """Cost approach valuation"""
        # Land value estimation
        land_area = property_data.get("land_area", property_data.get("area", 0))
        land_price_per_sqft = self._get_land_price_per_sqft(property_data)
        land_value = land_area * land_price_per_sqft
        
        # Construction cost estimation
        built_area = property_data.get("built_area", property_data.get("area", 0))
        construction_cost_per_sqft = self._get_construction_cost_per_sqft(property_data)
        construction_cost = built_area * construction_cost_per_sqft
        
        # Depreciation based on age
        property_age = property_data.get("age", 0)
        depreciation_rate = min(0.8, property_age * 0.02)  # 2% per year, max 80%
        depreciated_construction_cost = construction_cost * (1 - depreciation_rate)
        
        estimated_value = land_value + depreciated_construction_cost
        
        return PropertyValuation(
            estimated_value=estimated_value,
            confidence_score=0.7,
            valuation_method=PropertyValuationMethod.COST_APPROACH,
            comparable_properties=[],
            market_factors={
                "land_value": land_value,
                "construction_cost": construction_cost,
                "depreciated_construction_cost": depreciated_construction_cost,
                "depreciation_rate": depreciation_rate,
                "property_age": property_age
            },
            last_updated=datetime.utcnow()
        )
    
    def _avm_valuation(self, property_data: Dict[str, Any]) -> PropertyValuation:
        """Automated Valuation Model using multiple factors"""
        # Combine multiple approaches
        cma_valuation = self._cma_valuation(property_data)
        income_valuation = self._income_approach_valuation(property_data)
        cost_valuation = self._cost_approach_valuation(property_data)
        
        # Weighted average based on property type and data availability
        weights = self._get_valuation_weights(property_data)
        
        estimated_value = (
            cma_valuation.estimated_value * weights["cma"] +
            income_valuation.estimated_value * weights["income"] +
            cost_valuation.estimated_value * weights["cost"]
        )
        
        # Average confidence score
        confidence_score = (
            cma_valuation.confidence_score * weights["cma"] +
            income_valuation.confidence_score * weights["income"] +
            cost_valuation.confidence_score * weights["cost"]
        )
        
        return PropertyValuation(
            estimated_value=estimated_value,
            confidence_score=confidence_score,
            valuation_method=PropertyValuationMethod.AUTOMATED_VALUATION_MODEL,
            comparable_properties=cma_valuation.comparable_properties,
            market_factors={
                "cma_value": cma_valuation.estimated_value,
                "income_value": income_valuation.estimated_value,
                "cost_value": cost_valuation.estimated_value,
                "weights": weights
            },
            last_updated=datetime.utcnow()
        )
    
    # Market Analysis Methods
    
    def analyze_market_trends(self, area: str, property_type: str = None) -> MarketAnalysis:
        """Analyze market trends for a specific area"""
        try:
            # Get recent property data for the area
            recent_properties = self._get_recent_properties_in_area(area, property_type)
            
            if not recent_properties:
                return MarketAnalysis(
                    area=area,
                    average_price_per_sqft=0,
                    price_trend=MarketTrend.STABLE,
                    demand_supply_ratio=1.0,
                    growth_rate=0.0,
                    risk_assessment=RiskLevel.MEDIUM,
                    market_factors={"note": "Insufficient data for analysis"}
                )
            
            # Calculate average price per sqft
            total_price = sum(prop["price"] for prop in recent_properties)
            total_area = sum(prop["area"] for prop in recent_properties)
            avg_price_per_sqft = total_price / total_area if total_area > 0 else 0
            
            # Analyze price trend
            price_trend = self._analyze_price_trend(recent_properties)
            
            # Calculate demand-supply ratio
            demand_supply_ratio = self._calculate_demand_supply_ratio(area)
            
            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(recent_properties)
            
            # Assess risk
            risk_assessment = self._assess_market_risk(
                price_trend, demand_supply_ratio, growth_rate
            )
            
            return MarketAnalysis(
                area=area,
                average_price_per_sqft=avg_price_per_sqft,
                price_trend=price_trend,
                demand_supply_ratio=demand_supply_ratio,
                growth_rate=growth_rate,
                risk_assessment=risk_assessment,
                market_factors={
                    "properties_analyzed": len(recent_properties),
                    "analysis_period": "last_6_months",
                    "property_type": property_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market trends: {str(e)}")
            return MarketAnalysis(
                area=area,
                average_price_per_sqft=0,
                price_trend=MarketTrend.STABLE,
                demand_supply_ratio=1.0,
                growth_rate=0.0,
                risk_assessment=RiskLevel.MEDIUM,
                market_factors={"error": str(e)}
            )
    
    # Booking Rules Methods
    
    def validate_booking_request(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate booking request against business rules"""
        validation_result = {
            "is_valid": True,
            "requires_approval": False,
            "violations": [],
            "recommendations": [],
            "pricing_adjustments": {}
        }
        
        try:
            for rule in self.booking_rules:
                if not rule.is_active:
                    continue
                
                rule_result = self._evaluate_booking_rule(rule, booking_data)
                
                if rule_result["violated"]:
                    validation_result["violations"].append({
                        "rule": rule.rule_name,
                        "message": rule_result["message"],
                        "severity": rule_result["severity"]
                    })
                    
                    if rule.action == "reject_booking":
                        validation_result["is_valid"] = False
                    elif rule.action == "require_approval":
                        validation_result["requires_approval"] = True
                    elif rule.action == "apply_premium":
                        validation_result["pricing_adjustments"][rule.rule_name] = rule_result["adjustment"]
                
                if rule_result.get("recommendation"):
                    validation_result["recommendations"].append(rule_result["recommendation"])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating booking request: {str(e)}")
            return {
                "is_valid": False,
                "requires_approval": True,
                "violations": [{"rule": "system_error", "message": str(e), "severity": "high"}],
                "recommendations": [],
                "pricing_adjustments": {}
            }
    
    # Helper Methods
    
    def _find_comparable_properties(self, property_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find comparable properties for CMA"""
        # This would query the database for similar properties
        # For now, return mock data
        return [
            {
                "id": 1,
                "price": property_data.get("price", 0) * 0.95,
                "area": property_data.get("area", 0) * 1.1,
                "location": property_data.get("city", ""),
                "sold_date": datetime.utcnow() - timedelta(days=30)
            },
            {
                "id": 2,
                "price": property_data.get("price", 0) * 1.05,
                "area": property_data.get("area", 0) * 0.9,
                "location": property_data.get("city", ""),
                "sold_date": datetime.utcnow() - timedelta(days=45)
            }
        ]
    
    def _apply_property_adjustments(
        self, 
        base_price_per_sqft: float, 
        property_data: Dict[str, Any]
    ) -> float:
        """Apply property-specific adjustments to base price"""
        adjusted_price = base_price_per_sqft
        
        # Location adjustment
        location_type = property_data.get("location_type", "residential_area")
        location_factor = self.pricing_factors["location_premium"].get(location_type, 1.0)
        adjusted_price *= location_factor
        
        # Age adjustment
        age = property_data.get("age", 5)
        if age <= 5:
            age_factor = self.pricing_factors["property_age"]["0_5_years"]
        elif age <= 10:
            age_factor = self.pricing_factors["property_age"]["5_10_years"]
        elif age <= 20:
            age_factor = self.pricing_factors["property_age"]["10_20_years"]
        else:
            age_factor = self.pricing_factors["property_age"]["20_plus_years"]
        
        adjusted_price *= age_factor
        
        # Amenities adjustment
        amenities = property_data.get("amenities", [])
        for amenity in amenities:
            amenity_factor = self.pricing_factors["amenities"].get(amenity, 0)
            adjusted_price *= (1 + amenity_factor)
        
        return adjusted_price
    
    def _estimate_rental_income(self, property_data: Dict[str, Any]) -> float:
        """Estimate monthly rental income"""
        area = property_data.get("area", 0)
        city = property_data.get("city", "")
        
        # Base rent per sqft by city (mock data)
        base_rent_per_sqft = {
            "Mumbai": 80,
            "Delhi": 70,
            "Bangalore": 60,
            "Chennai": 50,
            "Hyderabad": 45,
            "Pune": 55
        }.get(city, 40)
        
        return area * base_rent_per_sqft
    
    def _get_capitalization_rate(self, property_data: Dict[str, Any]) -> float:
        """Get capitalization rate for income approach"""
        property_type = property_data.get("property_type", "apartment")
        location = property_data.get("city", "")
        
        # Base cap rates by property type and location
        base_cap_rates = {
            "apartment": 0.06,
            "house": 0.07,
            "commercial": 0.08,
            "villa": 0.065
        }
        
        # Location adjustments
        location_adjustments = {
            "Mumbai": -0.01,
            "Delhi": -0.005,
            "Bangalore": 0,
            "Chennai": 0.005,
            "Hyderabad": 0.01
        }
        
        base_rate = base_cap_rates.get(property_type, 0.07)
        location_adj = location_adjustments.get(location, 0)
        
        return base_rate + location_adj
    
    def _get_land_price_per_sqft(self, property_data: Dict[str, Any]) -> float:
        """Get land price per sqft"""
        city = property_data.get("city", "")
        
        # Mock land prices by city
        land_prices = {
            "Mumbai": 15000,
            "Delhi": 12000,
            "Bangalore": 8000,
            "Chennai": 6000,
            "Hyderabad": 5000,
            "Pune": 7000
        }
        
        return land_prices.get(city, 4000)
    
    def _get_construction_cost_per_sqft(self, property_data: Dict[str, Any]) -> float:
        """Get construction cost per sqft"""
        property_type = property_data.get("property_type", "apartment")
        
        # Construction costs by property type
        construction_costs = {
            "apartment": 2500,
            "house": 2000,
            "villa": 3000,
            "commercial": 3500
        }
        
        return construction_costs.get(property_type, 2500)
    
    def _get_valuation_weights(self, property_data: Dict[str, Any]) -> Dict[str, float]:
        """Get weights for different valuation methods"""
        property_type = property_data.get("property_type", "apartment")
        
        if property_type == "commercial":
            return {"cma": 0.3, "income": 0.6, "cost": 0.1}
        elif property_type in ["apartment", "house"]:
            return {"cma": 0.6, "income": 0.3, "cost": 0.1}
        else:
            return {"cma": 0.5, "income": 0.3, "cost": 0.2}
    
    def _get_recent_properties_in_area(
        self, 
        area: str, 
        property_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get recent properties in area for market analysis"""
        # This would query the database
        # For now, return mock data
        return [
            {
                "price": 5000000,
                "area": 1000,
                "created_at": datetime.utcnow() - timedelta(days=30),
                "property_type": "apartment"
            },
            {
                "price": 4500000,
                "area": 900,
                "created_at": datetime.utcnow() - timedelta(days=60),
                "property_type": "apartment"
            }
        ]
    
    def _analyze_price_trend(self, properties: List[Dict[str, Any]]) -> MarketTrend:
        """Analyze price trend from property data"""
        if len(properties) < 2:
            return MarketTrend.STABLE
        
        # Sort by date
        sorted_props = sorted(properties, key=lambda x: x["created_at"])
        
        # Calculate price per sqft trend
        recent_avg = sum(p["price"] / p["area"] for p in sorted_props[-3:]) / min(3, len(sorted_props))
        older_avg = sum(p["price"] / p["area"] for p in sorted_props[:3]) / min(3, len(sorted_props))
        
        change_percent = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        if change_percent > 0.1:
            return MarketTrend.BULLISH
        elif change_percent < -0.1:
            return MarketTrend.BEARISH
        else:
            return MarketTrend.STABLE
    
    def _calculate_demand_supply_ratio(self, area: str) -> float:
        """Calculate demand-supply ratio"""
        # Mock calculation
        return 1.2  # Indicates higher demand than supply
    
    def _calculate_growth_rate(self, properties: List[Dict[str, Any]]) -> float:
        """Calculate annual growth rate"""
        # Mock calculation
        return 0.08  # 8% annual growth
    
    def _assess_market_risk(
        self, 
        price_trend: MarketTrend, 
        demand_supply_ratio: float, 
        growth_rate: float
    ) -> RiskLevel:
        """Assess market risk level"""
        risk_score = 0
        
        if price_trend == MarketTrend.BEARISH:
            risk_score += 2
        elif price_trend == MarketTrend.VOLATILE:
            risk_score += 3
        
        if demand_supply_ratio < 0.8:
            risk_score += 2
        elif demand_supply_ratio > 1.5:
            risk_score += 1
        
        if growth_rate < 0:
            risk_score += 2
        elif growth_rate > 0.15:
            risk_score += 1
        
        if risk_score >= 4:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _evaluate_booking_rule(
        self, 
        rule: BookingRule, 
        booking_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a specific booking rule"""
        result = {
            "violated": False,
            "message": "",
            "severity": "low",
            "adjustment": 0,
            "recommendation": None
        }
        
        if rule.rule_name == "prevent_double_booking":
            # Check for conflicting bookings
            # This would query the database
            result["violated"] = False  # Mock result
            
        elif rule.rule_name == "minimum_advance_booking":
            booking_time = booking_data.get("preferred_date")
            if booking_time and (booking_time - datetime.utcnow()).total_seconds() < 24 * 3600:
                result["violated"] = True
                result["message"] = "Booking must be made at least 24 hours in advance"
                result["severity"] = "medium"
                
        elif rule.rule_name == "weekend_premium":
            booking_time = booking_data.get("preferred_date")
            if booking_time and booking_time.weekday() >= 5:  # Saturday or Sunday
                result["violated"] = True
                result["message"] = "Weekend premium applies"
                result["severity"] = "low"
                result["adjustment"] = 0.2  # 20% premium
                
        return result
