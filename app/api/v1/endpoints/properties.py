from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import uuid
from app.db import crud
from app.db.session import get_db
from app.schemas.properties import PropertyCreate, PropertyUpdate, PropertyOut
from app.core.security import get_current_active_user
from app.core.ai_services import ai_service
from app.utils.notifications import create_notification
# from app.core.document_manager import document_manager, save_property_image, save_property_video, save_property_document
from app.core.advanced_search import search_properties, get_search_suggestions, get_similar_properties
from app.core.property_comparison import compare_properties
from app.core.analytics_engine import get_property_analytics
import logging

logger = logging.getLogger(__name__)

# Optional authentication function
async def get_optional_current_user(
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None"""
    try:
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from fastapi import Request

        # This is a simplified version - in production you'd properly handle optional auth
        return None
    except:
        return None


router = APIRouter()

@router.post("/", response_model=PropertyOut)
async def create_property(
    property_data: PropertyCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new property with AI-powered fraud detection
    """
    try:
        if not getattr(current_user, 'kyc_verified', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="KYC verification is required to create a property"
            )

        # AI-powered fraud detection
        property_dict = property_data.model_dump()
        fraud_analysis = await ai_service.detect_fraud(
            property_data=property_dict,
            user_data={
                "email": getattr(current_user, 'email', ''),
                "phone": getattr(current_user, 'phone', ''),
                "name": getattr(current_user, 'name', ''),
                "properties_posted": len(crud.get_properties_by_owners(db, getattr(current_user, 'id'), "available")),
                "kyc_verified": getattr(current_user, 'kyc_verified', False)
            }
        )

        # If fraud score is too high, reject property creation
        if fraud_analysis.get("is_fraud", False) and fraud_analysis.get("confidence", 0) > 0.6:
            await create_notification(
                db=db,
                user_id=getattr(current_user, 'id'),
                title="Property Listing Rejected",
                message="Your property listing requires manual review due to security concerns.",
                notification_type="property_rejected"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Property listing rejected: {', '.join(fraud_analysis.get('reasons', ['Security check failed']))}"
            )

        # Create property
        new_property = crud.create_property(
            db=db,
            property_data=property_dict,
            owner_id=getattr(current_user, 'id')
        )

        # Create success notification
        await create_notification(
            db=db,
            user_id=getattr(current_user, 'id'),
            title="Property Listed Successfully",
            message=f"Your property '{property_data.title}' has been listed successfully!",
            notification_type="property_created"
        )

        return new_property

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating property: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create property"
        )
@router.get("/", response_model=List[PropertyOut])
async def list_properties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all properties with pagination
    """
    return crud.get_properties(db, skip=skip, limit=limit)


@router.get("/recommendations")
async def get_ai_property_recommendations(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Get AI-powered property recommendations
    """
    try:
        # Get all properties for now (in production, this would be personalized)
        properties = crud.get_properties(db, skip=0, limit=limit)

        recommendations = []
        for prop in properties:
            recommendations.append({
                "id": prop.id,
                "title": prop.title,
                "price": prop.price,
                "bhk": prop.bhk,
                "area": prop.area,
                "city": prop.city,
                "property_type": prop.property_type,
                "score": 0.85,  # Mock AI score
                "reason": "Based on your preferences and market trends"
            })

        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "user_id": current_user.get("id") if current_user else None
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property recommendations"
        )


@router.post("/compare")
async def compare_multiple_properties(
    property_ids: dict,
    db: Session = Depends(get_db)
):
    """
    Compare multiple properties
    """
    try:
        ids = property_ids.get("property_ids", [])
        if not ids or len(ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 property IDs are required for comparison"
            )

        if len(ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot compare more than 5 properties at once"
            )

        # Get properties
        properties = []
        for prop_id in ids:
            prop = crud.get_property(db, property_id=prop_id)
            if not prop:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property with ID {prop_id} not found"
                )
            properties.append(prop)

        # Create comparison data
        comparison = {
            "properties": [
                {
                    "id": prop.id,
                    "title": prop.title,
                    "price": prop.price,
                    "bhk": prop.bhk,
                    "area": prop.area,
                    "city": prop.city,
                    "property_type": prop.property_type,
                    "furnishing": prop.furnishing,
                    "price_per_sqft": prop.price / prop.area if prop.area > 0 else 0
                }
                for prop in properties
            ],
            "comparison": {
                "price_range": {
                    "min": min(prop.price for prop in properties),
                    "max": max(prop.price for prop in properties)
                },
                "area_range": {
                    "min": min(prop.area for prop in properties),
                    "max": max(prop.area for prop in properties)
                },
                "best_value": min(properties, key=lambda p: p.price / p.area if p.area > 0 else float('inf')).id
            }
        }

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare properties"
        )


@router.get("/search")
async def search_properties_endpoint(
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bhk: Optional[int] = None,
    property_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search properties with filters (alternative endpoint)
    """
    try:
        # Build search filters
        filters = {}
        if city:
            filters["city"] = city
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if bhk is not None:
            filters["bhk"] = bhk
        if property_type:
            filters["property_type"] = property_type

        # Use the search functionality
        properties = crud.search_properties(db, skip=skip, limit=limit, **filters)

        return [
            {
                "id": prop.id,
                "title": prop.title,
                "price": prop.price,
                "bhk": prop.bhk,
                "area": prop.area,
                "city": prop.city,
                "state": prop.state,
                "property_type": prop.property_type,
                "furnishing": prop.furnishing,
                "address": prop.address,
                "latitude": prop.latitude,
                "longitude": prop.longitude,
                "created_at": prop.created_at
            }
            for prop in properties
        ]

    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search properties"
        )


@router.get("/{property_id}", response_model=dict)
async def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Get a specific property with AI-powered similar property recommendations
    """
    try:
        property_obj = crud.get_property(db, property_id=property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # Add to recently viewed if user is authenticated
        if current_user:
            crud.add_recently_viewed(
                db,
                user_id=getattr(current_user, 'id'),
                property_id=property_id
            )

        # Get AI-powered similar properties
        similar_properties = []
        try:
            similar = ai_service.get_similar_properties(db, property_id, top_n=5)
            similar_properties = [{
                "property_id": rec.property_id,
                "score": rec.score,
                "reasons": rec.reasons
            } for rec in similar]
        except Exception as e:
            logger.warning(f"Failed to get similar properties: {str(e)}")

        return {
            "property": PropertyOut.model_validate(property_obj),
            "similar_properties": similar_properties,
            "viewed_by_user": bool(current_user)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property"
        )

@router.get("/{property_id}/recommendations")
async def get_property_recommendations(
    property_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered recommendations for a specific property
    """
    try:
        # Verify property exists
        property_obj = crud.get_property(db, property_id=property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # Get similar properties using AI
        similar_properties = ai_service.get_similar_properties(db, property_id, top_n=limit)

        recommendations = []
        for rec in similar_properties:
            try:
                prop = crud.get_property(db, rec.property_id)
                if prop:
                    recommendations.append({
                        "property": PropertyOut.model_validate(prop),
                        "similarity_score": rec.score,
                        "reasons": rec.reasons
                    })
            except Exception as e:
                logger.warning(f"Failed to get property {rec.property_id}: {str(e)}")

        return {
            "base_property_id": property_id,
            "recommendations": recommendations,
            "total": len(recommendations)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property recommendations"
        )

@router.post("/{property_id}/images")
async def upload_property_images(
    property_id: int,
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    property = crud.get_property(db, property_id=property_id)
    if not property:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Property not found"
        )
    if property.owner_id != current_user.id: # type: ignore
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You are not the owner of this property"
        )
    
    image_urls = []
    for image in images:
        file_ext = os.path.splitext(image.filename)[1] # type: ignore
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"app/static/images/properties/{filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
            
        image_url = f"/static/images/properties/{filename}"
        image_urls.append(image_url)
        
    return crud.app_property_images(db, property_id=property_id, image_urls=image_urls) # type: ignore


# @router.post("/{property_id}/documents")
# async def upload_property_documents(
#     property_id: int,
#     documents: List[UploadFile] = File(...),
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_active_user)
# ):
#     """Upload property documents (legal papers, certificates, etc.)"""
#     property = crud.get_property(db, property_id=property_id)
#     if not property:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Property not found"
#         )
#     if property.owner_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You are not the owner of this property"
#         )

#     uploaded_documents = []
#     for document in documents:
#         try:
#             doc_info = save_property_document(document, property_id, current_user.id)
#             uploaded_documents.append(doc_info)
#         except Exception as e:
#             logger.error(f"Error uploading document: {e}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to upload document: {str(e)}"
#             )

#     return {"message": "Documents uploaded successfully", "documents": uploaded_documents}


@router.get("/{property_id}/similar")
async def get_similar_properties_endpoint(
    property_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get properties similar to the specified property"""
    try:
        similar_props = get_similar_properties(db, property_id, limit)
        return {
            "property_id": property_id,
            "similar_properties": [
                {
                    "id": prop.id,
                    "title": prop.title,
                    "price": prop.price,
                    "bhk": prop.bhk,
                    "area": prop.area,
                    "city": prop.city,
                    "property_type": prop.property_type,
                    "furnishing": prop.furnishing
                }
                for prop in similar_props
            ]
        }
    except Exception as e:
        logger.error(f"Error getting similar properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get similar properties"
        )


@router.get("/{property_id}/analytics")
async def get_property_analytics_endpoint(
    property_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get detailed analytics for a property (owner only)"""
    property = crud.get_property(db, property_id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Only property owner can view analytics
    if property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view analytics for your own properties"
        )

    try:
        analytics = get_property_analytics(db, property_id, days)
        return analytics
    except Exception as e:
        logger.error(f"Error getting property analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property analytics"
        )


# Duplicate compare function removed - using the one defined earlier
        

@router.put("/{property_id}/status")
async def update_property_status(
    property_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    property = crud.get_property(db, property_id = property_id)
    if not property:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, # type: ignore
            detail = "Property not found"
        )
    if property.owner_id != current_user.id: # pyright: ignore[reportAttributeAccessIssue]
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN, # type: ignore
            detail = "You are not the owner of this property"
        )
    return crud.update_property_status(db, property_id=property_id, status=status) # type: ignore


# Duplicate function removed - using the one defined earlier


@router.post("/compare")
async def compare_multiple_properties(
    property_ids: dict,
    db: Session = Depends(get_db)
):
    """
    Compare multiple properties
    """
    try:
        ids = property_ids.get("property_ids", [])
        if not ids or len(ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 property IDs are required for comparison"
            )

        if len(ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot compare more than 5 properties at once"
            )

        # Get properties
        properties = []
        for prop_id in ids:
            prop = crud.get_property(db, property_id=prop_id)
            if not prop:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property with ID {prop_id} not found"
                )
            properties.append(prop)

        # Create comparison data
        comparison = {
            "properties": [
                {
                    "id": prop.id,
                    "title": prop.title,
                    "price": prop.price,
                    "bhk": prop.bhk,
                    "area": prop.area,
                    "city": prop.city,
                    "property_type": prop.property_type,
                    "furnishing": prop.furnishing,
                    "price_per_sqft": prop.price / prop.area if prop.area > 0 else 0
                }
                for prop in properties
            ],
            "comparison": {
                "price_range": {
                    "min": min(prop.price for prop in properties),
                    "max": max(prop.price for prop in properties)
                },
                "area_range": {
                    "min": min(prop.area for prop in properties),
                    "max": max(prop.area for prop in properties)
                },
                "best_value": min(properties, key=lambda p: p.price / p.area if p.area > 0 else float('inf')).id
            }
        }

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare properties"
        )


# Duplicate search function removed - using the one defined earlier