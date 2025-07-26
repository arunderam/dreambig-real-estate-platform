from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db import crud
from app.db.session import get_db
from app.schemas.users import UserInDB, UserUpdate, UserPreferences
from app.core.security import get_current_active_user
from app.core.ai_services import ai_service
from app.utils.notifications import create_notification
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/me", response_model=UserInDB)
async def read_user_me(
    current_user: UserInDB = Depends(get_current_active_user)
):
    return current_user

@router.put("/me", response_model=UserInDB)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")

        # Note: Phone number uniqueness will be handled by database constraints

        updated_user = crud.update_user(db, user_id=current_user.id, user_update=update_data)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")

        # Handle specific database errors
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg:
            if "phone" in error_msg:
                detail = "Phone number is already in use by another user"
            else:
                detail = "This information is already in use by another user"
        else:
            detail = f"Failed to update profile: {error_msg}"

        raise HTTPException(status_code=500, detail=detail)

@router.post("/favorites/{property_id}")
async def add_to_favorites(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    try:
        # Check if property exists
        property = crud.get_property(db, property_id=property_id)
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

        # Check if already in favorites
        existing_favorites = crud.get_favorites(db, user_id=current_user.id)
        if any(fav.property_id == property_id for fav in existing_favorites):
            raise HTTPException(status_code=400, detail="Property already in favorites")

        favorite = crud.add_favorite(db, user_id=current_user.id, property_id=property_id)
        return {"message": "Added to favorites", "favorite_id": favorite.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite for user {current_user.id}, property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to add to favorites"
        )

@router.get("/favorites", response_model=List[int])
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    try:
        favorites = crud.get_favorites(db, user_id=current_user.id)
        return [fav.property_id for fav in favorites]
    except Exception as e:
        logger.error(f"Error getting favorites for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load favorites"
        )

@router.get("/recently-viewed", response_model=List[int])
async def get_recently_viewed_properties(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user),
    limit: int = 10
):
    recently_viewed = crud.get_recently_viewed(db, user_id=current_user.id, limit=limit)
    return [item.property_id for item in recently_viewed]

@router.delete("/favorites/{property_id}")
async def remove_from_favorites(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    try:
        success = crud.remove_favorite(db, user_id=current_user.id, property_id=property_id)
        if not success:
            raise HTTPException(status_code=404, detail="Favorite not found")
        return {"message": "Removed from favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite for user {current_user.id}, property {property_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to remove from favorites"
        )

@router.get("/notifications")
async def get_notifications(
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    return crud.get_user_notifications(db, user_id=current_user.id, is_read=is_read) # type: ignore

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    notification = crud.mark_notification_as_read(db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.get("/recommendations")
async def get_personalized_recommendations(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get AI-powered personalized property recommendations for the user
    """
    try:
        # Get user's recently viewed properties for better recommendations
        recently_viewed = crud.get_recently_viewed(db, user_id=getattr(current_user, 'id'), limit=5)

        recommendations = []
        if recently_viewed:
            # Get similar properties based on recently viewed
            for viewed in recently_viewed:
                try:
                    similar = ai_service.get_similar_properties(
                        db,
                        getattr(viewed, 'property_id'),
                        top_n=3
                    )
                    recommendations.extend([{
                        "property_id": rec.property_id,
                        "score": rec.score,
                        "reasons": rec.reasons,
                        "based_on": "recently_viewed"
                    } for rec in similar])
                except Exception as e:
                    logger.warning(f"Failed to get similar properties: {str(e)}")

        # If user is an investor, get investment recommendations
        if getattr(current_user, 'role') == 'investor':
            try:
                investment_recs = await ai_service.get_investment_recommendations(
                    getattr(current_user, 'id'),
                    db
                )
                recommendations.extend([{
                    **rec,
                    "based_on": "investment_profile"
                } for rec in investment_recs])
            except Exception as e:
                logger.warning(f"Failed to get investment recommendations: {str(e)}")

        # Remove duplicates and limit results
        seen_properties = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec["property_id"] not in seen_properties:
                seen_properties.add(rec["property_id"])
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

        return {
            "recommendations": unique_recommendations,
            "total": len(unique_recommendations),
            "user_role": getattr(current_user, 'role')
        }

    except Exception as e:
        logger.error(f"Error getting recommendations for user {getattr(current_user, 'id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get recommendations"
        )

@router.post("/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update user preferences and get new AI-powered recommendations
    """
    try:
        # Update user preferences in database
        preferences_dict = preferences.model_dump(exclude_none=True)
        updated_user = crud.update_user(
            db,
            user_id=getattr(current_user, 'id'),
            user_update={"preferences": preferences_dict}
        )

        # Get new recommendations based on updated preferences
        new_recommendations = []
        if preferences_dict:
            try:
                # Get properties matching preferences
                properties = crud.get_properties(db, skip=0, limit=20, filters=preferences_dict)
                if properties:
                    for prop in properties[:5]:
                        similar = ai_service.get_similar_properties(
                            db,
                            getattr(prop, 'id'),
                            top_n=2
                        )
                        new_recommendations.extend([{
                            "property_id": rec.property_id,
                            "score": rec.score,
                            "reasons": rec.reasons
                        } for rec in similar])
            except Exception as e:
                logger.warning(f"Failed to generate new recommendations: {str(e)}")

        # Create notification about updated preferences
        await create_notification(
            db=db,
            user_id=getattr(current_user, 'id'),
            title="Preferences Updated",
            message="Your preferences have been updated. Check out new recommendations!",
            notification_type="preferences_updated"
        )

        return {
            "user": UserInDB.model_validate(updated_user),
            "new_recommendations": new_recommendations[:10],
            "message": "Preferences updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update preferences"
        )

@router.get("/analytics")
async def get_user_analytics(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get AI-powered analytics and insights for the user
    """
    try:
        user_id = getattr(current_user, 'id')

        # Get user activity data
        favorites = crud.get_favorites(db, user_id)
        recently_viewed = crud.get_recently_viewed(db, user_id, limit=20)

        # Calculate user behavior insights
        analytics = {
            "total_favorites": len(favorites),
            "total_viewed": len(recently_viewed),
            "activity_score": min(100, (len(favorites) * 5 + len(recently_viewed) * 2)),
            "user_type": "active" if len(recently_viewed) > 10 else "casual",
            "recommendations_accuracy": 85.5,  # This would be calculated based on user interactions
        }

        # Get property type preferences from user activity
        property_type_counts = {}
        for viewed in recently_viewed:
            try:
                prop = crud.get_property(db, getattr(viewed, 'property_id'))
                if prop:
                    prop_type = getattr(prop, 'property_type', 'unknown')
                    property_type_counts[prop_type] = property_type_counts.get(prop_type, 0) + 1
            except Exception:
                continue

        analytics["preferred_property_types"] = dict(sorted(
            property_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        # Get investment insights if user is an investor
        if getattr(current_user, 'role') == 'investor':
            try:
                investments = crud.get_investments_by_user(db, user_id)
                analytics["investment_insights"] = {
                    "total_investments": len(investments),
                    "portfolio_value": sum(getattr(inv, 'amount', 0) for inv in investments),
                    "risk_profile": "moderate"  # This would be calculated based on investment history
                }
            except Exception as e:
                logger.warning(f"Failed to get investment insights: {str(e)}")

        return analytics

    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user analytics"
        )


