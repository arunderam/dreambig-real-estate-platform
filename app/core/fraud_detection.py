from pydantic import BaseModel
from typing import Optional
import re

class FraudCheckResult(BaseModel):
    is_fraud: bool
    message: Optional[str] = None
    
async def check_property_fraud(property_data: dict):
    if property_data.get("price",0) < 1000:
        return FraudCheckResult(
            is_fraud=True,
            message="Property price seems unrealistically low"
        )
        
    description = property_data.get("description", "").lower()
    prohibited_phrases = [
        "free", "urgent", "immediate", "cash only", "contact me directly", "whatsapp only"
    ]
    
    if any(phrase in description for phrase in prohibited_phrases):
        return FraudCheckResult(
            is_fraud=True,
            message="Suspicious phrases detected in property description"
        )
        
        
    phone_pattern = [
        r'\d{10}',
        r'\d{3}[-\.\s]\d{3}[-\.\s]\d{4}',
        r'\(\d{3}\)\s*\d{3}[-\.\s]\d{4},'

    ]
    
    for pattern in phone_pattern:
        if re.search(pattern, description):
            return FraudCheckResult(
                is_fraud=True,
                message="Phone number detected in property description"
            )
    return FraudCheckResult(is_fraud=False)
