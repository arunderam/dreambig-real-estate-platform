import logging
from typing import List, Dict, Optional
from pydantic import BaseModel
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.db.session import get_db
from app.db import crud, models
from sqlalchemy.orm import Session
from app.config import settings
import requests
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationResult(BaseModel):
    property_id: int
    score: float
    reasons: List[str]

class AIService:
    def __init__(self):
        # Initialize ML models and components
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.property_vectors = None
        self.property_ids = None
        
        # External AI service configuration
        self.ai_service_url = settings.AI_SERVICE_URL if hasattr(settings, 'AI_SERVICE_URL') else None
        self.ai_service_key = settings.AI_SERVICE_KEY if hasattr(settings, 'AI_SERVICE_KEY') else None

    def initialize_property_vectors(self, db: Session):
        """Initialize property vectors for recommendation system"""
        try:
            properties = db.query(models.Property).filter(
                models.Property.status == models.PropertyStatus.AVAILABLE
            ).all()
            
            if not properties:
                logger.warning("No available properties found for vector initialization")
                return
            
            property_texts = [
                f"{p.title} {p.description} {p.city} {p.property_type.value} {p.furnishing.value}"
                for p in properties
            ]
            
            self.property_vectors = self.tfidf_vectorizer.fit_transform(property_texts)
            self.property_ids = [p.id for p in properties]
            logger.info(f"Initialized vectors for {len(properties)} properties")
            
        except Exception as e:
            logger.error(f"Error initializing property vectors: {str(e)}")
            raise

    def get_similar_properties(self, db: Session, property_id: int, top_n: int = 5) -> List[RecommendationResult]:
        """Get similar properties using content-based filtering"""
        try:
            if self.property_vectors is None:
                self.initialize_property_vectors(db)
                
            target_property = crud.get_property(db, property_id)
            if not target_property:
                raise ValueError("Property not found")
                
            target_text = (
                f"{target_property.title} {target_property.description} "
                f"{target_property.city} {target_property.property_type.value} "
                f"{target_property.furnishing.value}"
            )
            
            target_vector = self.tfidf_vectorizer.transform([target_text])
            similarities = cosine_similarity(target_vector, self.property_vectors)
            
            # Get top N similar properties (excluding itself)
            sim_scores = list(enumerate(similarities[0]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = [score for score in sim_scores if self.property_ids[score[0]] != property_id][:top_n] # type: ignore
            
            results = []
            for idx, score in sim_scores:
                reasons = []
                if score > 0.7:
                    reasons.append("Highly similar description")
                elif score > 0.4:
                    reasons.append("Similar features")
                else:
                    reasons.append("Partial match")
                
                results.append(RecommendationResult(
                    property_id=self.property_ids[idx], # type: ignore
                    score=float(score),
                    reasons=reasons
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in get_similar_properties: {str(e)}")
            return []

    async def detect_fraud(self, property_data: dict, user_data: dict) -> dict:
        """Detect potential fraud using AI analysis"""
        try:
            if self.ai_service_url:
                # Use external AI service if available
                payload = {
                    "property": property_data,
                    "user": user_data
                }
                headers = {
                    "Authorization": f"Bearer {self.ai_service_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    f"{self.ai_service_url}/detect-fraud",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=5
                )
                
                if response.status_code == 200:
                    return response.json()
            
            # Fallback to local rules if external service not available
            return self._local_fraud_detection(property_data, user_data)
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}")
            return {
                "is_fraud": False,
                "confidence": 0.0,
                "reasons": ["Error in analysis"]
            }

    def _local_fraud_detection(self, property_data: dict, user_data: dict) -> dict:
        """Local fraud detection rules"""
        reasons = []
        is_fraud = False
        
        # Price anomaly detection
        avg_price_per_sqft = {
            "apartment": 8000,
            "house": 6000,
            "villa": 10000,
            "plot": 3000,
            "commercial": 12000
        }
        
        prop_type = property_data.get("property_type", "").lower()
        if prop_type in avg_price_per_sqft:
            expected_price = avg_price_per_sqft[prop_type] * property_data.get("area", 1)
            if property_data.get("price", 0) < expected_price * 0.5:
                is_fraud = True
                reasons.append("Price significantly below market average")
        
        # Description analysis
        description = property_data.get("description", "").lower()
        suspicious_phrases = [
            "urgent sale", "quick transaction", "cash only",
            "contact directly", "whatsapp only", "no broker"
        ]
        
        for phrase in suspicious_phrases:
            if phrase in description:
                is_fraud = True
                reasons.append(f"Suspicious phrase found: '{phrase}'")
                break
                
        # User behavior
        if user_data.get("properties_posted", 0) > 5 and not user_data.get("kyc_verified", False):
            is_fraud = True
            reasons.append("User has posted many properties without KYC")
            
        return {
            "is_fraud": is_fraud,
            "confidence": 0.8 if is_fraud else 0.1,
            "reasons": reasons if reasons else ["No suspicious patterns detected"]
        }

    async def generate_agreement(self, booking_data: dict) -> dict:
        """Generate rental/service agreement using AI"""
        try:
            if self.ai_service_url:
                response = requests.post(
                    f"{self.ai_service_url}/generate-agreement",
                    headers={
                        "Authorization": f"Bearer {self.ai_service_key}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps(booking_data),
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
            
            # Fallback template
            return {
                "agreement_text": self._basic_agreement_template(booking_data),
                "status": "generated"
            }
            
        except Exception as e:
            logger.error(f"Error generating agreement: {str(e)}")
            return {
                "agreement_text": "Error generating agreement",
                "status": "error"
            }

    def _basic_agreement_template(self, booking_data: dict) -> str:
        """Basic agreement template fallback"""
        return f"""
        AGREEMENT FOR {booking_data.get('service_type', 'SERVICE').upper()}
        
        This agreement is made between:
        - Service Provider: {booking_data.get('provider_name', 'N/A')}
        - Client: {booking_data.get('user_name', 'N/A')}
        
        Service Details: {booking_data.get('details', {}).get('description', 'N/A')}
        Duration: {booking_data.get('details', {}).get('duration', 'N/A')}
        Terms and Conditions apply.
        
        Signed on: {booking_data.get('created_at', 'N/A')}
        """

    async def get_investment_recommendations(self, user_id: int, db: Session) -> List[dict]:
        """Get personalized investment recommendations"""
        try:
            user = crud.get_user(db, user_id)
            if not user:
                return []
                
            # Get user's past investments
            past_investments = crud.get_investments_by_user(db, user_id)
            
            # Simple recommendation logic (in production, use proper ML)
            properties = db.query(models.Property).filter(
                models.Property.status == models.PropertyStatus.AVAILABLE,
                models.Property.price <= self._get_user_budget(user, past_investments)
            ).order_by(models.Property.price.desc()).limit(5).all()
            
            return [{
                "property_id": p.id,
                "title": p.title,
                "expected_roi": self._estimate_roi(p),
                "risk_level": self._assess_risk(p),
                "reasons": ["Matches your investment profile"]
            } for p in properties]
            
        except Exception as e:
            logger.error(f"Error in investment recommendations: {str(e)}")
            return []

    def _get_user_budget(self, user: models.User, past_investments: list) -> float:
        """Estimate user's investment budget"""
        if past_investments:
            avg_investment = sum(i.amount for i in past_investments) / len(past_investments)
            return avg_investment * 1.5
        return 1000000  # Default budget

    def _estimate_roi(self, property: models.Property) -> float:
        """Estimate ROI for a property"""
        base_roi = {
            "apartment": 7.5,
            "house": 6.0,
            "villa": 8.0,
            "plot": 10.0,
            "commercial": 12.0
        }.get(property.property_type.value, 5.0)
        
        # Adjust based on location
        if "bangalore" in property.city.lower():
            base_roi += 1.5
        elif "mumbai" in property.city.lower():
            base_roi += 2.0
            
        return base_roi

    def _assess_risk(self, property: models.Property) -> str:
        """Assess risk level for a property"""
        if property.property_type.value in ["apartment", "house"]:
            return "low"
        elif property.property_type.value == "commercial":
            return "high"
        return "medium"

# Singleton instance
ai_service = AIService()