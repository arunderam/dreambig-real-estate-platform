"""
Enhanced validation utilities for DreamBig application
"""
import re
import phonenumbers
from typing import Optional, List, Dict, Any
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, validator
import bleach
from urllib.parse import urlparse

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

def validate_email_address(email: str) -> str:
    """Validate and normalize email address"""
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError as e:
        raise ValidationError("email", str(e))

def validate_phone_number(phone: str, country_code: str = "IN") -> str:
    """Validate and format phone number"""
    try:
        parsed = phonenumbers.parse(phone, country_code)
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError("phone", "Invalid phone number")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException as e:
        raise ValidationError("phone", f"Invalid phone number: {str(e)}")

def validate_password(password: str) -> str:
    """Validate password strength"""
    if len(password) < 8:
        raise ValidationError("password", "Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        raise ValidationError("password", "Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        raise ValidationError("password", "Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        raise ValidationError("password", "Password must contain at least one digit")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("password", "Password must contain at least one special character")
    
    return password

def validate_pincode(pincode: str, country: str = "IN") -> str:
    """Validate postal/pin code"""
    if country == "IN":
        if not re.match(r"^[1-9][0-9]{5}$", pincode):
            raise ValidationError("pincode", "Invalid Indian PIN code format")
    else:
        # Generic validation for other countries
        if not re.match(r"^[A-Za-z0-9\s-]{3,10}$", pincode):
            raise ValidationError("pincode", "Invalid postal code format")
    
    return pincode

def validate_coordinates(latitude: float, longitude: float) -> tuple:
    """Validate geographical coordinates"""
    if not (-90 <= latitude <= 90):
        raise ValidationError("latitude", "Latitude must be between -90 and 90")
    
    if not (-180 <= longitude <= 180):
        raise ValidationError("longitude", "Longitude must be between -180 and 180")
    
    return latitude, longitude

def validate_price(price: float, min_price: float = 0) -> float:
    """Validate property price"""
    if price < min_price:
        raise ValidationError("price", f"Price must be at least {min_price}")
    
    if price > 1000000000:  # 100 crores
        raise ValidationError("price", "Price seems unreasonably high")
    
    return price

def validate_area(area: float) -> float:
    """Validate property area"""
    if area <= 0:
        raise ValidationError("area", "Area must be greater than 0")
    
    if area > 100000:  # 100,000 sq ft
        raise ValidationError("area", "Area seems unreasonably large")
    
    return area

def validate_bhk(bhk: int) -> int:
    """Validate BHK (bedroom, hall, kitchen) count"""
    if bhk < 0:
        raise ValidationError("bhk", "BHK cannot be negative")
    
    if bhk > 20:
        raise ValidationError("bhk", "BHK count seems unreasonably high")
    
    return bhk

def sanitize_html(content: str, allowed_tags: List[str] = None) -> str:
    """Sanitize HTML content to prevent XSS"""
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    
    allowed_attributes = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def validate_url(url: str) -> str:
    """Validate URL format"""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError("url", "Invalid URL format")
        return url
    except Exception:
        raise ValidationError("url", "Invalid URL format")

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> str:
    """Validate file extension"""
    if '.' not in filename:
        raise ValidationError("file", "File must have an extension")
    
    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in [ext.lower() for ext in allowed_extensions]:
        raise ValidationError("file", f"File extension must be one of: {', '.join(allowed_extensions)}")
    
    return filename

def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> int:
    """Validate file size (default max 10MB)"""
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError("file", f"File size must be less than {max_mb}MB")
    
    return file_size

def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate JSON structure has required fields"""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError("json", f"Missing required fields: {', '.join(missing_fields)}")
    
    return data

def validate_indian_pan(pan: str) -> str:
    """Validate Indian PAN card number"""
    pan = pan.upper().strip()
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan):
        raise ValidationError("pan", "Invalid PAN card format")
    
    return pan

def validate_indian_aadhar(aadhar: str) -> str:
    """Validate Indian Aadhar number"""
    aadhar = re.sub(r'\s+', '', aadhar)  # Remove spaces
    if not re.match(r"^[0-9]{12}$", aadhar):
        raise ValidationError("aadhar", "Invalid Aadhar number format")
    
    return aadhar

def validate_investment_amount(amount: float, min_amount: float = 1000) -> float:
    """Validate investment amount"""
    if amount < min_amount:
        raise ValidationError("amount", f"Minimum investment amount is {min_amount}")
    
    if amount > 100000000:  # 10 crores
        raise ValidationError("amount", "Investment amount seems unreasonably high")
    
    return amount

def validate_roi_percentage(roi: float) -> float:
    """Validate ROI percentage"""
    if roi < 0:
        raise ValidationError("roi", "ROI cannot be negative")
    
    if roi > 100:
        raise ValidationError("roi", "ROI percentage seems unreasonably high")
    
    return roi

class PropertyValidator:
    """Property-specific validation class"""
    
    @staticmethod
    def validate_property_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete property data"""
        validated_data = {}
        
        # Required fields
        required_fields = ['title', 'price', 'property_type', 'city', 'state']
        validate_json_structure(data, required_fields)
        
        # Validate individual fields
        validated_data['title'] = sanitize_html(data['title'])
        validated_data['description'] = sanitize_html(data.get('description', ''))
        validated_data['price'] = validate_price(float(data['price']))
        
        if 'area' in data:
            validated_data['area'] = validate_area(float(data['area']))
        
        if 'bhk' in data:
            validated_data['bhk'] = validate_bhk(int(data['bhk']))
        
        if 'pincode' in data:
            validated_data['pincode'] = validate_pincode(data['pincode'])
        
        if 'latitude' in data and 'longitude' in data:
            lat, lng = validate_coordinates(float(data['latitude']), float(data['longitude']))
            validated_data['latitude'] = lat
            validated_data['longitude'] = lng
        
        # Copy other validated fields
        for field in ['property_type', 'furnishing', 'address', 'city', 'state']:
            if field in data:
                validated_data[field] = sanitize_html(str(data[field]))
        
        return validated_data

class UserValidator:
    """User-specific validation class"""
    
    @staticmethod
    def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user registration data"""
        validated_data = {}
        
        # Required fields
        required_fields = ['email', 'password', 'name']
        validate_json_structure(data, required_fields)
        
        # Validate individual fields
        validated_data['email'] = validate_email_address(data['email'])
        validated_data['password'] = validate_password(data['password'])
        validated_data['name'] = sanitize_html(data['name'])
        
        if 'phone' in data and data['phone']:
            validated_data['phone'] = validate_phone_number(data['phone'])
        
        return validated_data
