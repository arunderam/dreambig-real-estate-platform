from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.db import crud
from app.db.session import get_db
from app.core.ai_services import ai_service
from app.schemas.properties import PropertyOut
from app.core.advanced_search import search_properties, get_search_suggestions
from app.core.analytics_engine import get_market_analytics
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Optional authentication function
async def get_optional_current_user() -> Optional[dict]:
    """Get current user if authenticated, otherwise return None"""
    # For now, return None to make search work without authentication
    # In production, you'd implement proper optional authentication
    return None

@router.get("/", response_model=dict)
async def search_properties(
    query: Optional[str] = None,
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    bhk: Optional[int] = Query(None, ge=1),
    property_type: Optional[str] = None,
    furnishing: Optional[str] = None,
    location: Optional[str] = None,
    verified_owner: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    AI-powered property search with intelligent filtering and recommendations
    """
    try:
        filters = {
            "price_min": price_min,
            "price_max": price_max,
            "bhk": bhk,
            "property_type": property_type,
            "furnishing": furnishing,
            "location": location,
            "verified_owner": verified_owner,
        }

        # Get base properties using filters
        properties = crud.get_properties(db, skip=skip, limit=limit, filters=filters)

        # Apply text search if query is provided
        if query:
            # Enhanced search with AI-like scoring
            scored_properties = []
            query_lower = query.lower()

            for prop in properties:
                score = 0
                title_lower = getattr(prop, 'title', '').lower()
                desc_lower = getattr(prop, 'description', '').lower()
                city_lower = getattr(prop, 'city', '').lower()

                # Title match gets highest score
                if query_lower in title_lower:
                    score += 10
                # Description match gets medium score
                if query_lower in desc_lower:
                    score += 5
                # Location match gets medium score
                if query_lower in city_lower:
                    score += 7

                # Word-based matching for better results
                query_words = query_lower.split()
                for word in query_words:
                    if word in title_lower:
                        score += 3
                    if word in desc_lower:
                        score += 2
                    if word in city_lower:
                        score += 2

                if score > 0:
                    scored_properties.append((prop, score))

            # Sort by score and extract properties
            scored_properties.sort(key=lambda x: x[1], reverse=True)
            properties = [prop for prop, score in scored_properties]

        # Get AI-powered recommendations if user is authenticated
        recommendations = []
        if current_user and properties:
            try:
                # Get similar properties for the first few results
                for prop in properties[:3]:
                    similar = ai_service.get_similar_properties(
                        db,
                        getattr(prop, 'id'),
                        top_n=2
                    )
                    recommendations.extend([{
                        "property_id": rec.property_id,
                        "score": rec.score,
                        "reasons": rec.reasons,
                        "based_on": getattr(prop, 'id')
                    } for rec in similar])
            except Exception as e:
                logger.warning(f"Failed to get AI recommendations: {str(e)}")

        # Convert properties to response format
        property_results = []
        for prop in properties:
            try:
                property_results.append(PropertyOut.model_validate(prop))
            except Exception as e:
                logger.warning(f"Failed to validate property {getattr(prop, 'id', 'unknown')}: {str(e)}")

        return {
            "properties": property_results,
            "total": len(property_results),
            "recommendations": recommendations[:5],  # Limit recommendations
            "search_query": query,
            "filters_applied": {k: v for k, v in filters.items() if v is not None},
            "has_more": len(properties) == limit
        }

    except Exception as e:
        logger.error(f"Error in property search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Search failed. Please try again."
        )

@router.get("/smart-suggestions")
async def get_smart_search_suggestions(
    query: str,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Get AI-powered search suggestions based on user query
    """
    try:
        # Get all properties for analysis
        all_properties = crud.get_properties(db, skip=0, limit=1000)

        suggestions = {
            "locations": set(),
            "property_types": set(),
            "price_ranges": [],
            "similar_searches": []
        }

        query_lower = query.lower()

        # Extract suggestions from existing properties
        for prop in all_properties:
            city = getattr(prop, 'city', '').lower()
            prop_type = getattr(prop, 'property_type', '')
            title = getattr(prop, 'title', '').lower()

            # Location suggestions
            if query_lower in city:
                suggestions["locations"].add(getattr(prop, 'city', ''))

            # Property type suggestions
            if query_lower in str(prop_type).lower():
                suggestions["property_types"].add(str(prop_type))

            # Similar search suggestions based on title
            if any(word in title for word in query_lower.split()):
                suggestions["similar_searches"].append(getattr(prop, 'title', ''))

        # Convert sets to lists and limit results
        return {
            "query": query,
            "suggestions": {
                "locations": list(suggestions["locations"])[:10],
                "property_types": list(suggestions["property_types"])[:5],
                "similar_searches": suggestions["similar_searches"][:10]
            }
        }

    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get search suggestions"
        )


@router.get("/advanced")
async def advanced_search(
    query: Optional[str] = None,
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    bhk: Optional[int] = Query(None, ge=0),
    property_type: Optional[str] = None,
    furnishing: Optional[str] = None,
    city: Optional[str] = None,
    verified_only: Optional[bool] = None,
    sort_by: Optional[str] = Query("relevance", regex="^(price|area|date|relevance)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Advanced property search with intelligent filtering and ranking
    """
    try:
        # Build filters
        filters = {}
        if price_min is not None:
            filters["price_min"] = price_min
        if price_max is not None:
            filters["price_max"] = price_max
        if bhk is not None:
            filters["bhk"] = bhk
        if property_type:
            filters["property_type"] = property_type
        if furnishing:
            filters["furnishing"] = furnishing
        if city:
            filters["city"] = city
        if verified_only is not None:
            filters["verified_only"] = verified_only

        # Get user preferences if available
        user_preferences = None
        if current_user:
            user_preferences = {
                "budget_range": [price_min or 0, price_max or float('inf')],
                "preferred_locations": [city] if city else [],
                "preferred_property_types": [property_type] if property_type else []
            }

        # Perform advanced search
        properties, total = search_properties(
            db=db,
            query=query,
            filters=filters,
            user_preferences=user_preferences,
            skip=skip,
            limit=limit
        )

        # Convert to response format
        property_results = []
        for prop in properties:
            try:
                property_results.append(PropertyOut.model_validate(prop))
            except Exception as e:
                logger.warning(f"Failed to validate property {prop.id}: {str(e)}")

        return {
            "properties": property_results,
            "total": total,
            "count": len(property_results),
            "search_query": query,
            "filters_applied": filters,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "has_more": len(property_results) == limit
            }
        }

    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Advanced search failed. Please try again."
        )


@router.get("/suggestions")
async def get_enhanced_search_suggestions(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Get intelligent search suggestions based on query
    """
    try:
        suggestions = get_search_suggestions(db, query)
        return {
            "query": query,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error getting enhanced suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get search suggestions"
        )


@router.get("/market-analytics")
async def get_market_analytics_endpoint(
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get market analytics for specified criteria
    """
    try:
        analytics = get_market_analytics(db, city, property_type, days)
        return analytics
    except Exception as e:
        logger.error(f"Error getting market analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get market analytics"
        )