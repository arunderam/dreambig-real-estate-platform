"""
Property comparison system with detailed analysis
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from geopy.distance import geodesic

from app.db import models
from app.db.crud import get_property

logger = logging.getLogger(__name__)

class PropertyComparator:
    """Advanced property comparison with detailed analysis"""
    
    def __init__(self):
        self.comparison_factors = {
            "price": {"weight": 0.25, "type": "numeric", "lower_is_better": True},
            "area": {"weight": 0.20, "type": "numeric", "lower_is_better": False},
            "bhk": {"weight": 0.15, "type": "numeric", "lower_is_better": False},
            "location_score": {"weight": 0.15, "type": "numeric", "lower_is_better": False},
            "property_age": {"weight": 0.10, "type": "numeric", "lower_is_better": True},
            "verification_status": {"weight": 0.10, "type": "boolean", "lower_is_better": False},
            "furnishing_level": {"weight": 0.05, "type": "categorical", "lower_is_better": False}
        }
        
        self.furnishing_scores = {
            "furnished": 3,
            "semi_furnished": 2,
            "unfurnished": 1
        }
        
        self.property_type_scores = {
            "villa": 5,
            "house": 4,
            "apartment": 3,
            "commercial": 2,
            "plot": 1
        }
    
    def compare_properties(
        self, 
        db: Session, 
        property_ids: List[int],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Compare multiple properties with detailed analysis"""
        
        if len(property_ids) < 2:
            raise ValueError("At least 2 properties are required for comparison")
        
        if len(property_ids) > 5:
            raise ValueError("Maximum 5 properties can be compared at once")
        
        # Fetch properties
        properties = []
        for prop_id in property_ids:
            prop = get_property(db, prop_id)
            if prop:
                properties.append(prop)
        
        if len(properties) < 2:
            raise ValueError("Could not find enough valid properties for comparison")
        
        # Perform comparison
        comparison_result = {
            "properties": [],
            "comparison_matrix": {},
            "recommendations": {},
            "summary": {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Calculate scores for each property
        property_scores = {}
        for prop in properties:
            scores = self._calculate_property_scores(prop, properties, user_preferences)
            property_scores[prop.id] = scores
        
        # Build comparison matrix
        comparison_result["comparison_matrix"] = self._build_comparison_matrix(
            properties, property_scores
        )
        
        # Generate property summaries
        for prop in properties:
            prop_data = {
                "id": prop.id,
                "title": prop.title,
                "price": prop.price,
                "bhk": prop.bhk,
                "area": prop.area,
                "property_type": prop.property_type,
                "furnishing": prop.furnishing,
                "city": prop.city,
                "address": prop.address,
                "is_verified": prop.is_verified,
                "created_at": prop.created_at.isoformat(),
                "scores": property_scores[prop.id],
                "pros": self._get_property_pros(prop, properties),
                "cons": self._get_property_cons(prop, properties)
            }
            comparison_result["properties"].append(prop_data)
        
        # Generate recommendations
        comparison_result["recommendations"] = self._generate_recommendations(
            properties, property_scores, user_preferences
        )
        
        # Generate summary
        comparison_result["summary"] = self._generate_comparison_summary(
            properties, property_scores
        )
        
        return comparison_result
    
    def _calculate_property_scores(
        self, 
        property_obj: models.Property, 
        all_properties: List[models.Property],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """Calculate various scores for a property"""
        scores = {}
        
        # Price per sqft score
        price_per_sqft = property_obj.price / property_obj.area if property_obj.area > 0 else 0
        all_price_per_sqft = [p.price / p.area for p in all_properties if p.area > 0]
        if all_price_per_sqft:
            min_price_per_sqft = min(all_price_per_sqft)
            max_price_per_sqft = max(all_price_per_sqft)
            if max_price_per_sqft > min_price_per_sqft:
                scores["price_efficiency"] = 1 - (price_per_sqft - min_price_per_sqft) / (max_price_per_sqft - min_price_per_sqft)
            else:
                scores["price_efficiency"] = 1.0
        else:
            scores["price_efficiency"] = 0.5
        
        # Area score (normalized)
        all_areas = [p.area for p in all_properties]
        min_area, max_area = min(all_areas), max(all_areas)
        if max_area > min_area:
            scores["area_score"] = (property_obj.area - min_area) / (max_area - min_area)
        else:
            scores["area_score"] = 1.0
        
        # BHK score
        all_bhks = [p.bhk for p in all_properties]
        max_bhk = max(all_bhks)
        scores["bhk_score"] = property_obj.bhk / max_bhk if max_bhk > 0 else 0
        
        # Furnishing score
        scores["furnishing_score"] = self.furnishing_scores.get(property_obj.furnishing, 1) / 3
        
        # Property type score
        scores["property_type_score"] = self.property_type_scores.get(property_obj.property_type, 1) / 5
        
        # Verification score
        scores["verification_score"] = 1.0 if property_obj.is_verified else 0.0
        
        # Age score (newer is better)
        property_age_days = (datetime.utcnow() - property_obj.created_at).days
        all_ages = [(datetime.utcnow() - p.created_at).days for p in all_properties]
        min_age, max_age = min(all_ages), max(all_ages)
        if max_age > min_age:
            scores["freshness_score"] = 1 - (property_age_days - min_age) / (max_age - min_age)
        else:
            scores["freshness_score"] = 1.0
        
        # Overall score
        scores["overall_score"] = (
            scores["price_efficiency"] * 0.25 +
            scores["area_score"] * 0.20 +
            scores["bhk_score"] * 0.15 +
            scores["property_type_score"] * 0.15 +
            scores["furnishing_score"] * 0.10 +
            scores["verification_score"] * 0.10 +
            scores["freshness_score"] * 0.05
        )
        
        # User preference adjustments
        if user_preferences:
            preference_bonus = 0
            
            # Budget preference
            if user_preferences.get("budget_range"):
                min_budget, max_budget = user_preferences["budget_range"]
                if min_budget <= property_obj.price <= max_budget:
                    preference_bonus += 0.1
            
            # Location preference
            if user_preferences.get("preferred_locations"):
                for location in user_preferences["preferred_locations"]:
                    if location.lower() in property_obj.city.lower():
                        preference_bonus += 0.1
                        break
            
            # Property type preference
            if user_preferences.get("preferred_property_types"):
                if property_obj.property_type in user_preferences["preferred_property_types"]:
                    preference_bonus += 0.05
            
            scores["overall_score"] = min(1.0, scores["overall_score"] + preference_bonus)
        
        return scores
    
    def _build_comparison_matrix(
        self, 
        properties: List[models.Property], 
        property_scores: Dict[int, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Build detailed comparison matrix"""
        matrix = {
            "factors": [
                {"name": "Price", "key": "price", "format": "currency"},
                {"name": "Area (sqft)", "key": "area", "format": "number"},
                {"name": "BHK", "key": "bhk", "format": "number"},
                {"name": "Property Type", "key": "property_type", "format": "text"},
                {"name": "Furnishing", "key": "furnishing", "format": "text"},
                {"name": "Location", "key": "city", "format": "text"},
                {"name": "Verified", "key": "is_verified", "format": "boolean"},
                {"name": "Price/sqft", "key": "price_per_sqft", "format": "currency"},
                {"name": "Overall Score", "key": "overall_score", "format": "percentage"}
            ],
            "data": []
        }
        
        for prop in properties:
            price_per_sqft = prop.price / prop.area if prop.area > 0 else 0
            row = {
                "property_id": prop.id,
                "price": prop.price,
                "area": prop.area,
                "bhk": prop.bhk,
                "property_type": prop.property_type.title(),
                "furnishing": prop.furnishing.replace("_", " ").title(),
                "city": prop.city,
                "is_verified": prop.is_verified,
                "price_per_sqft": price_per_sqft,
                "overall_score": property_scores[prop.id]["overall_score"]
            }
            matrix["data"].append(row)
        
        return matrix
    
    def _get_property_pros(
        self, 
        property_obj: models.Property, 
        all_properties: List[models.Property]
    ) -> List[str]:
        """Get property advantages"""
        pros = []
        
        # Price advantages
        prices = [p.price for p in all_properties]
        if property_obj.price == min(prices):
            pros.append("Lowest price among compared properties")
        elif property_obj.price < sum(prices) / len(prices):
            pros.append("Below average price")
        
        # Area advantages
        areas = [p.area for p in all_properties]
        if property_obj.area == max(areas):
            pros.append("Largest area among compared properties")
        
        # BHK advantages
        bhks = [p.bhk for p in all_properties]
        if property_obj.bhk == max(bhks):
            pros.append("Most bedrooms among compared properties")
        
        # Verification
        if property_obj.is_verified:
            verified_count = sum(1 for p in all_properties if p.is_verified)
            if verified_count < len(all_properties):
                pros.append("Verified property")
        
        # Furnishing
        if property_obj.furnishing == "furnished":
            furnished_count = sum(1 for p in all_properties if p.furnishing == "furnished")
            if furnished_count < len(all_properties):
                pros.append("Fully furnished")
        
        # Property type
        if property_obj.property_type in ["villa", "house"]:
            pros.append("Independent property")
        
        return pros
    
    def _get_property_cons(
        self, 
        property_obj: models.Property, 
        all_properties: List[models.Property]
    ) -> List[str]:
        """Get property disadvantages"""
        cons = []
        
        # Price disadvantages
        prices = [p.price for p in all_properties]
        if property_obj.price == max(prices):
            cons.append("Highest price among compared properties")
        elif property_obj.price > sum(prices) / len(prices) * 1.2:
            cons.append("Significantly above average price")
        
        # Area disadvantages
        areas = [p.area for p in all_properties]
        if property_obj.area == min(areas):
            cons.append("Smallest area among compared properties")
        
        # Verification
        if not property_obj.is_verified:
            cons.append("Property not verified")
        
        # Furnishing
        if property_obj.furnishing == "unfurnished":
            cons.append("Unfurnished property")
        
        return cons
    
    def _generate_recommendations(
        self, 
        properties: List[models.Property], 
        property_scores: Dict[int, Dict[str, float]],
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate recommendations based on comparison"""
        
        # Sort by overall score
        sorted_properties = sorted(
            properties, 
            key=lambda p: property_scores[p.id]["overall_score"], 
            reverse=True
        )
        
        recommendations = {
            "best_overall": {
                "property_id": sorted_properties[0].id,
                "title": sorted_properties[0].title,
                "reason": "Highest overall score based on all factors"
            },
            "best_value": None,
            "most_spacious": None,
            "budget_friendly": None
        }
        
        # Best value (price efficiency)
        best_value_prop = max(
            properties, 
            key=lambda p: property_scores[p.id]["price_efficiency"]
        )
        recommendations["best_value"] = {
            "property_id": best_value_prop.id,
            "title": best_value_prop.title,
            "reason": "Best price per square foot"
        }
        
        # Most spacious
        most_spacious_prop = max(properties, key=lambda p: p.area)
        recommendations["most_spacious"] = {
            "property_id": most_spacious_prop.id,
            "title": most_spacious_prop.title,
            "reason": f"Largest area ({most_spacious_prop.area} sqft)"
        }
        
        # Budget friendly
        budget_friendly_prop = min(properties, key=lambda p: p.price)
        recommendations["budget_friendly"] = {
            "property_id": budget_friendly_prop.id,
            "title": budget_friendly_prop.title,
            "reason": f"Lowest price (₹{budget_friendly_prop.price:,.0f})"
        }
        
        return recommendations
    
    def _generate_comparison_summary(
        self, 
        properties: List[models.Property], 
        property_scores: Dict[int, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Generate comparison summary statistics"""
        
        prices = [p.price for p in properties]
        areas = [p.area for p in properties]
        
        return {
            "total_properties": len(properties),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices)
            },
            "area_range": {
                "min": min(areas),
                "max": max(areas),
                "average": sum(areas) / len(areas)
            },
            "verified_count": sum(1 for p in properties if p.is_verified),
            "property_types": list(set(p.property_type for p in properties)),
            "cities": list(set(p.city for p in properties))
        }

# Global comparator instance
property_comparator = PropertyComparator()

# Convenience function
def compare_properties(
    db: Session, 
    property_ids: List[int], 
    user_preferences: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Compare properties with detailed analysis"""
    return property_comparator.compare_properties(db, property_ids, user_preferences)
