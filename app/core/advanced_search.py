"""
Advanced search system with intelligent filtering and recommendations
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from datetime import datetime, timedelta
import logging
from geopy.distance import geodesic
import json

from app.db import models
from app.core.ai_services import ai_service

logger = logging.getLogger(__name__)

class AdvancedSearchEngine:
    """Advanced search engine with AI-powered features"""
    
    def __init__(self):
        self.search_weights = {
            "title": 3.0,
            "description": 2.0,
            "location": 2.5,
            "features": 1.5,
            "exact_match": 5.0
        }
        
        # Common search synonyms
        self.synonyms = {
            "apartment": ["flat", "unit", "condo"],
            "house": ["home", "bungalow", "villa"],
            "luxury": ["premium", "high-end", "upscale"],
            "cheap": ["affordable", "budget", "economical"],
            "spacious": ["large", "big", "roomy"],
            "modern": ["contemporary", "new", "updated"]
        }
    
    def parse_search_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language search query"""
        if not query:
            return {}
        
        query = query.lower().strip()
        parsed = {
            "keywords": [],
            "location": None,
            "price_range": None,
            "bhk": None,
            "property_type": None,
            "amenities": []
        }
        
        # Extract price range
        price_patterns = [
            r'(\d+)\s*(?:lakh|lac)\s*to\s*(\d+)\s*(?:lakh|lac)',
            r'(\d+)\s*(?:crore|cr)\s*to\s*(\d+)\s*(?:crore|cr)',
            r'under\s*(\d+)\s*(?:lakh|lac)',
            r'above\s*(\d+)\s*(?:lakh|lac)',
            r'₹\s*(\d+)\s*(?:lakh|lac)\s*to\s*₹\s*(\d+)\s*(?:lakh|lac)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, query)
            if match:
                if "to" in pattern:
                    min_price = int(match.group(1))
                    max_price = int(match.group(2))
                    if "crore" in pattern:
                        min_price *= 10000000
                        max_price *= 10000000
                    else:
                        min_price *= 100000
                        max_price *= 100000
                    parsed["price_range"] = [min_price, max_price]
                elif "under" in pattern:
                    max_price = int(match.group(1))
                    if "crore" in pattern:
                        max_price *= 10000000
                    else:
                        max_price *= 100000
                    parsed["price_range"] = [0, max_price]
                elif "above" in pattern:
                    min_price = int(match.group(1))
                    if "crore" in pattern:
                        min_price *= 10000000
                    else:
                        min_price *= 100000
                    parsed["price_range"] = [min_price, float('inf')]
                break
        
        # Extract BHK
        bhk_match = re.search(r'(\d+)\s*(?:bhk|bedroom|bed)', query)
        if bhk_match:
            parsed["bhk"] = int(bhk_match.group(1))
        
        # Extract property type
        property_types = ["apartment", "house", "villa", "plot", "commercial"]
        for prop_type in property_types:
            if prop_type in query:
                parsed["property_type"] = prop_type
                break
        
        # Extract location (common Indian cities)
        cities = [
            "bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune", 
            "kolkata", "ahmedabad", "jaipur", "surat", "lucknow", "kanpur",
            "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "pimpri"
        ]
        
        for city in cities:
            if city in query:
                parsed["location"] = city.title()
                break
        
        # Extract amenities
        amenities = [
            "parking", "gym", "swimming pool", "security", "lift", "garden",
            "playground", "club house", "power backup", "water supply"
        ]
        
        for amenity in amenities:
            if amenity in query:
                parsed["amenities"].append(amenity)
        
        # Extract remaining keywords
        words = query.split()
        stop_words = {"in", "at", "with", "for", "and", "or", "the", "a", "an", "is", "are"}
        
        for word in words:
            if (word not in stop_words and 
                len(word) > 2 and 
                not any(word in str(v) for v in parsed.values() if v)):
                parsed["keywords"].append(word)
        
        return parsed
    
    def build_search_query(
        self, 
        db: Session, 
        search_params: Dict[str, Any],
        filters: Dict[str, Any] = None # type: ignore # type: ignore
    ):
        """Build SQLAlchemy query from search parameters"""
        query = db.query(models.Property).filter(
            models.Property.status == models.PropertyStatus.AVAILABLE
        )
        
        # Apply filters
        if filters:
            if filters.get("price_min"):
                query = query.filter(models.Property.price >= filters["price_min"])
            
            if filters.get("price_max"):
                query = query.filter(models.Property.price <= filters["price_max"])
            
            if filters.get("bhk"):
                query = query.filter(models.Property.bhk == filters["bhk"])
            
            if filters.get("property_type"):
                query = query.filter(models.Property.property_type == filters["property_type"])
            
            if filters.get("furnishing"):
                query = query.filter(models.Property.furnishing == filters["furnishing"])
            
            if filters.get("city"):
                query = query.filter(models.Property.city.ilike(f"%{filters['city']}%"))
            
            if filters.get("verified_only"):
                query = query.filter(models.Property.is_verified == True)
        
        # Apply search parameters
        if search_params.get("price_range"):
            min_price, max_price = search_params["price_range"]
            if max_price != float('inf'):
                query = query.filter(
                    and_(
                        models.Property.price >= min_price,
                        models.Property.price <= max_price
                    )
                )
            else:
                query = query.filter(models.Property.price >= min_price)
        
        if search_params.get("bhk"):
            query = query.filter(models.Property.bhk == search_params["bhk"])
        
        if search_params.get("property_type"):
            query = query.filter(models.Property.property_type == search_params["property_type"])
        
        if search_params.get("location"):
            location = search_params["location"]
            query = query.filter(
                or_(
                    models.Property.city.ilike(f"%{location}%"),
                    models.Property.address.ilike(f"%{location}%"),
                    models.Property.state.ilike(f"%{location}%")
                )
            )
        
        # Text search on keywords
        if search_params.get("keywords"):
            keywords = search_params["keywords"]
            text_conditions = []
            
            for keyword in keywords:
                # Add synonyms
                search_terms = [keyword]
                for main_term, synonyms in self.synonyms.items():
                    if keyword in synonyms or keyword == main_term:
                        search_terms.extend([main_term] + synonyms)
                
                # Create search conditions
                for term in set(search_terms):
                    text_conditions.extend([
                        models.Property.title.ilike(f"%{term}%"),
                        models.Property.description.ilike(f"%{term}%"),
                        models.Property.address.ilike(f"%{term}%")
                    ])
            
            if text_conditions:
                query = query.filter(or_(*text_conditions))
        
        return query
    
    def calculate_relevance_score(
        self, 
        property_obj: models.Property, 
        search_params: Dict[str, Any],
        user_preferences: Dict[str, Any] = None # type: ignore # type: ignore
    ) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        
        # Base score
        score += 1.0
        
        # Keyword matching
        if search_params.get("keywords"):
            for keyword in search_params["keywords"]:
                if keyword.lower() in property_obj.title.lower():
                    score += self.search_weights["title"]
                if keyword.lower() in property_obj.description.lower():
                    score += self.search_weights["description"]
                if keyword.lower() in property_obj.address.lower():
                    score += self.search_weights["location"]
        
        # Exact matches
        if search_params.get("bhk") and property_obj.bhk == search_params["bhk"]:
            score += self.search_weights["exact_match"]
        
        if search_params.get("property_type") and property_obj.property_type == search_params["property_type"]:
            score += self.search_weights["exact_match"]
        
        # Price range matching
        if search_params.get("price_range"):
            min_price, max_price = search_params["price_range"]
            if min_price <= property_obj.price <= max_price:
                score += 2.0
        
        # Verification bonus
        if property_obj.is_verified: # type: ignore
            score += 1.5
        
        # Recency bonus
        days_old = (datetime.utcnow() - property_obj.created_at).days
        if days_old < 7:
            score += 1.0
        elif days_old < 30:
            score += 0.5
        
        # User preference matching
        if user_preferences:
            if user_preferences.get("preferred_locations"):
                for location in user_preferences["preferred_locations"]:
                    if location.lower() in property_obj.city.lower():
                        score += 2.0
            
            if user_preferences.get("budget_range"):
                min_budget, max_budget = user_preferences["budget_range"]
                if min_budget <= property_obj.price <= max_budget:
                    score += 1.5
        
        return score
    
    def get_search_suggestions(self, db: Session, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        
        if not query or len(query) < 2:
            return suggestions
        
        query = query.lower()
        
        # City suggestions
        cities = db.query(models.Property.city).distinct().all()
        for (city,) in cities:
            if city and query in city.lower():
                suggestions.append(city)
        
        # Property type suggestions
        property_types = ["Apartment", "House", "Villa", "Plot", "Commercial"]
        for prop_type in property_types:
            if query in prop_type.lower():
                suggestions.append(prop_type)
        
        # Common search terms
        common_terms = [
            "2 BHK Apartment", "3 BHK House", "Luxury Villa", 
            "Furnished Apartment", "Commercial Space", "Plot for Sale"
        ]
        
        for term in common_terms:
            if query in term.lower():
                suggestions.append(term)
        
        return suggestions[:limit]
    
    def get_similar_properties(
        self, 
        db: Session, 
        property_id: int, 
        limit: int = 5
    ) -> List[models.Property]:
        """Find similar properties based on current property"""
        base_property = db.query(models.Property).filter(
            models.Property.id == property_id
        ).first()
        
        if not base_property:
            return []
        
        # Build similarity query
        query = db.query(models.Property).filter(
            and_(
                models.Property.id != property_id,
                models.Property.status == models.PropertyStatus.AVAILABLE
            )
        )
        
        # Similar price range (±20%)
        price_margin = base_property.price * 0.2
        query = query.filter(
            and_(
                models.Property.price >= base_property.price - price_margin,
                models.Property.price <= base_property.price + price_margin
            )
        )
        
        # Same city or nearby
        query = query.filter(models.Property.city == base_property.city)
        
        # Same property type
        query = query.filter(models.Property.property_type == base_property.property_type)
        
        # Similar BHK (±1)
        query = query.filter(
            and_(
                models.Property.bhk >= max(0, base_property.bhk - 1), # type: ignore
                models.Property.bhk <= base_property.bhk + 1
            )
        )
        
        return query.limit(limit).all()

# Global search engine instance
search_engine = AdvancedSearchEngine()

# Convenience functions
def search_properties(
    db: Session,
    query: str = None, # type: ignore # type: ignore
    filters: Dict[str, Any] = None, # type: ignore # type: ignore
    user_preferences: Dict[str, Any] = None, # type: ignore
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[models.Property], int]:
    """Search properties with advanced filtering"""
    
    # Parse search query
    search_params = search_engine.parse_search_query(query) if query else {}
    
    # Build query
    db_query = search_engine.build_search_query(db, search_params, filters)
    
    # Get total count
    total = db_query.count()
    
    # Get results
    properties = db_query.offset(skip).limit(limit).all()
    
    # Calculate relevance scores and sort
    if query or user_preferences:
        property_scores = []
        for prop in properties:
            score = search_engine.calculate_relevance_score(prop, search_params, user_preferences)
            property_scores.append((prop, score))
        
        # Sort by relevance score
        property_scores.sort(key=lambda x: x[1], reverse=True)
        properties = [prop for prop, score in property_scores]
    
    return properties, total

def get_search_suggestions(db: Session, query: str) -> List[str]:
    """Get search suggestions"""
    return search_engine.get_search_suggestions(db, query)

def get_similar_properties(db: Session, property_id: int) -> List[models.Property]:
    """Get similar properties"""
    return search_engine.get_similar_properties(db, property_id)
