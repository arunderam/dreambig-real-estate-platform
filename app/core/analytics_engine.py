"""
Advanced analytics engine for property and user insights
"""
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from datetime import datetime, timedelta
import logging
from collections import defaultdict, Counter

from app.db import models

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Comprehensive analytics engine for business insights"""
    
    def __init__(self):
        self.cache_duration = timedelta(hours=1)
        self._cache = {}
    
    def get_property_analytics(
        self, 
        db: Session, 
        property_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific property"""
        
        property_obj = db.query(models.Property).filter(
            models.Property.id == property_id
        ).first()
        
        if not property_obj:
            raise ValueError(f"Property {property_id} not found")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            "property_id": property_id,
            "property_title": property_obj.title,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "performance_metrics": {},
            "market_comparison": {},
            "user_engagement": {},
            "recommendations": []
        }
        
        # Performance metrics
        analytics["performance_metrics"] = self._get_property_performance(
            db, property_obj, start_date, end_date
        )
        
        # Market comparison
        analytics["market_comparison"] = self._get_market_comparison(
            db, property_obj
        )
        
        # User engagement
        analytics["user_engagement"] = self._get_property_engagement(
            db, property_id, start_date, end_date
        )
        
        # Generate recommendations
        analytics["recommendations"] = self._generate_property_recommendations(
            property_obj, analytics
        )
        
        return analytics
    
    def get_user_analytics(
        self, 
        db: Session, 
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            "user_id": user_id,
            "user_name": user.name,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "activity_summary": {},
            "preferences": {},
            "engagement_patterns": {},
            "recommendations": []
        }
        
        # Activity summary
        analytics["activity_summary"] = self._get_user_activity(
            db, user_id, start_date, end_date
        )
        
        # User preferences
        analytics["preferences"] = self._analyze_user_preferences(db, user_id)
        
        # Engagement patterns
        analytics["engagement_patterns"] = self._get_user_engagement_patterns(
            db, user_id, start_date, end_date
        )
        
        # Generate recommendations
        analytics["recommendations"] = self._generate_user_recommendations(
            user, analytics
        )
        
        return analytics
    
    def get_market_analytics(
        self, 
        db: Session,
        city: str = None,
        property_type: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get market-wide analytics"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            "market_scope": {
                "city": city,
                "property_type": property_type,
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                }
            },
            "market_overview": {},
            "price_trends": {},
            "supply_demand": {},
            "popular_features": {},
            "growth_metrics": {}
        }
        
        # Build base query
        query = db.query(models.Property)
        if city:
            query = query.filter(models.Property.city.ilike(f"%{city}%"))
        if property_type:
            query = query.filter(models.Property.property_type == property_type)
        
        # Market overview
        analytics["market_overview"] = self._get_market_overview(query)
        
        # Price trends
        analytics["price_trends"] = self._get_price_trends(query, start_date, end_date)
        
        # Supply and demand
        analytics["supply_demand"] = self._get_supply_demand_metrics(
            db, city, property_type, start_date, end_date
        )
        
        # Popular features
        analytics["popular_features"] = self._get_popular_features(query)
        
        # Growth metrics
        analytics["growth_metrics"] = self._get_growth_metrics(
            query, start_date, end_date
        )
        
        return analytics
    
    def _get_property_performance(
        self, 
        db: Session, 
        property_obj: models.Property,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate property performance metrics"""
        
        # Simulated view tracking (in real app, you'd have a views table)
        days_since_creation = (datetime.utcnow() - property_obj.created_at).days
        estimated_views = max(1, days_since_creation * 2)  # Rough estimate
        
        # Calculate metrics
        price_per_sqft = property_obj.price / property_obj.area if property_obj.area > 0 else 0
        
        return {
            "total_views": estimated_views,
            "daily_average_views": estimated_views / max(1, days_since_creation),
            "price_per_sqft": price_per_sqft,
            "days_on_market": days_since_creation,
            "is_verified": property_obj.is_verified,
            "status": property_obj.status,
            "last_updated": property_obj.updated_at.isoformat() if property_obj.updated_at else None
        }
    
    def _get_market_comparison(
        self, 
        db: Session, 
        property_obj: models.Property
    ) -> Dict[str, Any]:
        """Compare property with market averages"""
        
        # Get similar properties for comparison
        similar_properties = db.query(models.Property).filter(
            and_(
                models.Property.city == property_obj.city,
                models.Property.property_type == property_obj.property_type,
                models.Property.bhk == property_obj.bhk,
                models.Property.id != property_obj.id
            )
        ).all()
        
        if not similar_properties:
            return {"message": "No similar properties found for comparison"}
        
        # Calculate market averages
        avg_price = sum(p.price for p in similar_properties) / len(similar_properties)
        avg_area = sum(p.area for p in similar_properties) / len(similar_properties)
        avg_price_per_sqft = avg_price / avg_area if avg_area > 0 else 0
        
        property_price_per_sqft = property_obj.price / property_obj.area if property_obj.area > 0 else 0
        
        return {
            "similar_properties_count": len(similar_properties),
            "market_averages": {
                "price": avg_price,
                "area": avg_area,
                "price_per_sqft": avg_price_per_sqft
            },
            "property_vs_market": {
                "price_difference_percent": ((property_obj.price - avg_price) / avg_price * 100) if avg_price > 0 else 0,
                "area_difference_percent": ((property_obj.area - avg_area) / avg_area * 100) if avg_area > 0 else 0,
                "price_per_sqft_difference_percent": ((property_price_per_sqft - avg_price_per_sqft) / avg_price_per_sqft * 100) if avg_price_per_sqft > 0 else 0
            },
            "market_position": self._determine_market_position(property_obj, similar_properties)
        }
    
    def _get_property_engagement(
        self, 
        db: Session, 
        property_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get property engagement metrics"""
        
        # Count favorites (if favorites table exists)
        favorites_count = db.query(models.Favorite).filter(
            models.Favorite.property_id == property_id
        ).count() if hasattr(models, 'Favorite') else 0
        
        # Simulated engagement metrics
        return {
            "total_favorites": favorites_count,
            "estimated_inquiries": max(1, favorites_count * 2),
            "engagement_score": min(100, favorites_count * 10 + 20),
            "social_shares": max(0, favorites_count // 2)
        }
    
    def _get_user_activity(
        self, 
        db: Session, 
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get user activity summary"""
        
        # Properties owned
        owned_properties = db.query(models.Property).filter(
            models.Property.owner_id == user_id
        ).count()
        
        # Investments made
        investments = db.query(models.Investment).filter(
            models.Investment.investor_id == user_id
        ).count() if hasattr(models, 'Investment') else 0
        
        # Favorites
        favorites = db.query(models.Favorite).filter(
            models.Favorite.user_id == user_id
        ).count() if hasattr(models, 'Favorite') else 0
        
        return {
            "properties_listed": owned_properties,
            "investments_made": investments,
            "properties_favorited": favorites,
            "profile_completion": self._calculate_profile_completion(db, user_id),
            "last_activity": datetime.utcnow().isoformat(),  # Simulated
            "activity_level": "high" if owned_properties + investments + favorites > 5 else "moderate" if owned_properties + investments + favorites > 2 else "low"
        }
    
    def _analyze_user_preferences(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze user preferences from their activity"""
        
        # Get user's favorited properties
        user_favorites = []
        if hasattr(models, 'Favorite'):
            favorites = db.query(models.Favorite).filter(
                models.Favorite.user_id == user_id
            ).all()
            
            for fav in favorites:
                prop = db.query(models.Property).filter(
                    models.Property.id == fav.property_id
                ).first()
                if prop:
                    user_favorites.append(prop)
        
        if not user_favorites:
            return {"message": "Not enough data to analyze preferences"}
        
        # Analyze preferences
        preferred_cities = Counter(p.city for p in user_favorites)
        preferred_types = Counter(p.property_type for p in user_favorites)
        preferred_bhk = Counter(p.bhk for p in user_favorites)
        
        avg_budget = sum(p.price for p in user_favorites) / len(user_favorites)
        
        return {
            "preferred_cities": dict(preferred_cities.most_common(3)),
            "preferred_property_types": dict(preferred_types.most_common(3)),
            "preferred_bhk": dict(preferred_bhk.most_common(3)),
            "average_budget": avg_budget,
            "budget_range": [
                min(p.price for p in user_favorites),
                max(p.price for p in user_favorites)
            ]
        }
    
    def _get_market_overview(self, query) -> Dict[str, Any]:
        """Get market overview statistics"""
        
        properties = query.all()
        
        if not properties:
            return {"message": "No properties found for the specified criteria"}
        
        prices = [p.price for p in properties]
        areas = [p.area for p in properties]
        
        return {
            "total_properties": len(properties),
            "price_statistics": {
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices),
                "median": sorted(prices)[len(prices) // 2]
            },
            "area_statistics": {
                "min": min(areas),
                "max": max(areas),
                "average": sum(areas) / len(areas)
            },
            "property_type_distribution": dict(Counter(p.property_type for p in properties)),
            "bhk_distribution": dict(Counter(p.bhk for p in properties)),
            "furnishing_distribution": dict(Counter(p.furnishing for p in properties)),
            "verified_percentage": (sum(1 for p in properties if p.is_verified) / len(properties)) * 100
        }
    
    def _determine_market_position(
        self, 
        property_obj: models.Property, 
        similar_properties: List[models.Property]
    ) -> str:
        """Determine property's market position"""
        
        prices = [p.price for p in similar_properties]
        avg_price = sum(prices) / len(prices)
        
        if property_obj.price > avg_price * 1.2:
            return "premium"
        elif property_obj.price < avg_price * 0.8:
            return "budget"
        else:
            return "market_rate"
    
    def _calculate_profile_completion(self, db: Session, user_id: int) -> float:
        """Calculate user profile completion percentage"""
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return 0.0
        
        completion_factors = {
            "name": bool(user.name),
            "email": bool(user.email),
            "phone": bool(user.phone),
            "is_verified": user.is_verified,
            "kyc_completed": hasattr(user, 'kyc_status') and getattr(user, 'kyc_status') == 'verified'
        }
        
        completed = sum(completion_factors.values())
        total = len(completion_factors)
        
        return (completed / total) * 100
    
    def _generate_property_recommendations(
        self, 
        property_obj: models.Property, 
        analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for property improvement"""
        
        recommendations = []
        
        # Performance-based recommendations
        performance = analytics.get("performance_metrics", {})
        if performance.get("daily_average_views", 0) < 2:
            recommendations.append("Consider updating property photos to increase visibility")
        
        if not property_obj.is_verified:
            recommendations.append("Get property verified to increase trust and visibility")
        
        # Market comparison recommendations
        market_comparison = analytics.get("market_comparison", {})
        if isinstance(market_comparison, dict) and "property_vs_market" in market_comparison:
            price_diff = market_comparison["property_vs_market"].get("price_difference_percent", 0)
            if price_diff > 20:
                recommendations.append("Consider reducing price as it's significantly above market average")
            elif price_diff < -20:
                recommendations.append("Property is priced below market - consider highlighting unique features")
        
        return recommendations
    
    def _generate_user_recommendations(
        self, 
        user: models.User, 
        analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for user"""
        
        recommendations = []
        
        activity = analytics.get("activity_summary", {})
        
        if activity.get("profile_completion", 0) < 80:
            recommendations.append("Complete your profile to get better property recommendations")
        
        if activity.get("properties_listed", 0) == 0:
            recommendations.append("List your first property to start earning")
        
        if activity.get("activity_level") == "low":
            recommendations.append("Explore more properties to get personalized recommendations")
        
        return recommendations

# Global analytics engine instance
analytics_engine = AnalyticsEngine()

# Convenience functions
def get_property_analytics(db: Session, property_id: int, days: int = 30) -> Dict[str, Any]:
    """Get property analytics"""
    return analytics_engine.get_property_analytics(db, property_id, days)

def get_user_analytics(db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
    """Get user analytics"""
    return analytics_engine.get_user_analytics(db, user_id, days)

def get_market_analytics(
    db: Session, 
    city: str = None, 
    property_type: str = None, 
    days: int = 30
) -> Dict[str, Any]:
    """Get market analytics"""
    return analytics_engine.get_market_analytics(db, city, property_type, days)
