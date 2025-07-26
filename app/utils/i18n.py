"""
Internationalization (i18n) utilities for DreamBig Real Estate Platform
"""
import json
import os
from typing import Dict, Optional, Any, List
from pathlib import Path
from enum import Enum
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

class SupportedLanguage(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"
    BENGALI = "bn"
    GUJARATI = "gu"
    MARATHI = "mr"
    PUNJABI = "pa"

class TranslationManager:
    """Manager for handling translations and localization"""
    
    def __init__(self):
        self.translations_dir = Path("app/translations")
        self.translations_dir.mkdir(exist_ok=True)
        self.default_language = SupportedLanguage.ENGLISH
        self._translations_cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_translations()
    
    def _load_all_translations(self):
        """Load all translation files into cache"""
        try:
            for language in SupportedLanguage:
                self._load_language_translations(language.value)
        except Exception as e:
            logger.error(f"Error loading translations: {str(e)}")
    
    def _load_language_translations(self, language_code: str):
        """Load translations for a specific language"""
        try:
            translation_file = self.translations_dir / f"{language_code}.json"
            
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self._translations_cache[language_code] = json.load(f)
            else:
                # Create default translation file if it doesn't exist
                self._create_default_translation_file(language_code)
                
        except Exception as e:
            logger.error(f"Error loading translations for {language_code}: {str(e)}")
            self._translations_cache[language_code] = {}
    
    def _create_default_translation_file(self, language_code: str):
        """Create default translation file with common keys"""
        default_translations = self._get_default_translations(language_code)
        
        translation_file = self.translations_dir / f"{language_code}.json"
        with open(translation_file, 'w', encoding='utf-8') as f:
            json.dump(default_translations, f, ensure_ascii=False, indent=2)
        
        self._translations_cache[language_code] = default_translations
    
    def _get_default_translations(self, language_code: str) -> Dict[str, Any]:
        """Get default translations for a language"""
        if language_code == SupportedLanguage.ENGLISH:
            return {
                "common": {
                    "welcome": "Welcome",
                    "login": "Login",
                    "logout": "Logout",
                    "register": "Register",
                    "search": "Search",
                    "filter": "Filter",
                    "sort": "Sort",
                    "save": "Save",
                    "cancel": "Cancel",
                    "delete": "Delete",
                    "edit": "Edit",
                    "view": "View",
                    "back": "Back",
                    "next": "Next",
                    "previous": "Previous",
                    "submit": "Submit",
                    "loading": "Loading...",
                    "error": "Error",
                    "success": "Success",
                    "warning": "Warning",
                    "info": "Information"
                },
                "navigation": {
                    "home": "Home",
                    "properties": "Properties",
                    "investments": "Investments",
                    "services": "Services",
                    "about": "About",
                    "contact": "Contact",
                    "dashboard": "Dashboard",
                    "profile": "Profile",
                    "settings": "Settings"
                },
                "property": {
                    "title": "Property",
                    "price": "Price",
                    "location": "Location",
                    "bedrooms": "Bedrooms",
                    "bathrooms": "Bathrooms",
                    "area": "Area",
                    "type": "Type",
                    "status": "Status",
                    "description": "Description",
                    "features": "Features",
                    "images": "Images",
                    "videos": "Videos",
                    "contact_owner": "Contact Owner",
                    "book_viewing": "Book Viewing",
                    "add_to_favorites": "Add to Favorites",
                    "share": "Share",
                    "similar_properties": "Similar Properties"
                },
                "booking": {
                    "book_property": "Book Property",
                    "viewing": "Viewing",
                    "rental_application": "Rental Application",
                    "purchase_offer": "Purchase Offer",
                    "inspection": "Inspection",
                    "preferred_date": "Preferred Date",
                    "preferred_time": "Preferred Time",
                    "duration": "Duration",
                    "contact_details": "Contact Details",
                    "special_requirements": "Special Requirements",
                    "booking_confirmed": "Booking Confirmed",
                    "booking_pending": "Booking Pending",
                    "booking_cancelled": "Booking Cancelled"
                },
                "forms": {
                    "name": "Name",
                    "email": "Email",
                    "phone": "Phone",
                    "password": "Password",
                    "confirm_password": "Confirm Password",
                    "address": "Address",
                    "city": "City",
                    "state": "State",
                    "pincode": "Pincode",
                    "required_field": "This field is required",
                    "invalid_email": "Please enter a valid email address",
                    "invalid_phone": "Please enter a valid phone number",
                    "password_mismatch": "Passwords do not match"
                },
                "messages": {
                    "welcome_message": "Welcome to DreamBig Real Estate Platform",
                    "login_success": "Login successful",
                    "logout_success": "Logout successful",
                    "registration_success": "Registration successful",
                    "booking_success": "Booking created successfully",
                    "profile_updated": "Profile updated successfully",
                    "property_saved": "Property saved successfully",
                    "error_occurred": "An error occurred. Please try again.",
                    "no_results": "No results found",
                    "loading_properties": "Loading properties...",
                    "unauthorized": "You are not authorized to perform this action"
                }
            }
        elif language_code == SupportedLanguage.HINDI:
            return {
                "common": {
                    "welcome": "स्वागत",
                    "login": "लॉगिन",
                    "logout": "लॉगआउट",
                    "register": "पंजीकरण",
                    "search": "खोजें",
                    "filter": "फिल्टर",
                    "sort": "क्रमबद्ध करें",
                    "save": "सेव करें",
                    "cancel": "रद्द करें",
                    "delete": "हटाएं",
                    "edit": "संपादित करें",
                    "view": "देखें",
                    "back": "वापस",
                    "next": "अगला",
                    "previous": "पिछला",
                    "submit": "जमा करें",
                    "loading": "लोड हो रहा है...",
                    "error": "त्रुटि",
                    "success": "सफलता",
                    "warning": "चेतावनी",
                    "info": "जानकारी"
                },
                "navigation": {
                    "home": "होम",
                    "properties": "संपत्तियां",
                    "investments": "निवेश",
                    "services": "सेवाएं",
                    "about": "हमारे बारे में",
                    "contact": "संपर्क",
                    "dashboard": "डैशबोर्ड",
                    "profile": "प्रोफाइल",
                    "settings": "सेटिंग्स"
                },
                "property": {
                    "title": "संपत्ति",
                    "price": "कीमत",
                    "location": "स्थान",
                    "bedrooms": "बेडरूम",
                    "bathrooms": "बाथरूम",
                    "area": "क्षेत्रफल",
                    "type": "प्रकार",
                    "status": "स्थिति",
                    "description": "विवरण",
                    "features": "विशेषताएं",
                    "images": "चित्र",
                    "videos": "वीडियो",
                    "contact_owner": "मालिक से संपर्क करें",
                    "book_viewing": "देखने की बुकिंग करें",
                    "add_to_favorites": "पसंदीदा में जोड़ें",
                    "share": "साझा करें",
                    "similar_properties": "समान संपत्तियां"
                }
            }
        else:
            # For other languages, return English as fallback
            return self._get_default_translations(SupportedLanguage.ENGLISH)
    
    @lru_cache(maxsize=1000)
    def get_translation(
        self, 
        key: str, 
        language: str = None, 
        default: str = None,
        **kwargs
    ) -> str:
        """Get translation for a key in specified language"""
        if language is None:
            language = self.default_language.value
        
        # Ensure language is supported
        if language not in [lang.value for lang in SupportedLanguage]:
            language = self.default_language.value
        
        # Get translation from cache
        translations = self._translations_cache.get(language, {})
        
        # Support nested keys like "common.welcome"
        keys = key.split('.')
        value = translations
        
        try:
            for k in keys:
                value = value[k]
            
            # Format string with kwargs if provided
            if kwargs and isinstance(value, str):
                value = value.format(**kwargs)
            
            return value
            
        except (KeyError, TypeError):
            # Fallback to English if key not found
            if language != self.default_language.value:
                return self.get_translation(key, self.default_language.value, default, **kwargs)
            
            # Return default or key if no translation found
            return default or key
    
    def get_language_info(self, language_code: str) -> Dict[str, str]:
        """Get language information"""
        language_info = {
            SupportedLanguage.ENGLISH: {
                "name": "English",
                "native_name": "English",
                "direction": "ltr"
            },
            SupportedLanguage.HINDI: {
                "name": "Hindi",
                "native_name": "हिन्दी",
                "direction": "ltr"
            },
            SupportedLanguage.TAMIL: {
                "name": "Tamil",
                "native_name": "தமிழ்",
                "direction": "ltr"
            },
            SupportedLanguage.TELUGU: {
                "name": "Telugu",
                "native_name": "తెలుగు",
                "direction": "ltr"
            },
            SupportedLanguage.KANNADA: {
                "name": "Kannada",
                "native_name": "ಕನ್ನಡ",
                "direction": "ltr"
            },
            SupportedLanguage.MALAYALAM: {
                "name": "Malayalam",
                "native_name": "മലയാളം",
                "direction": "ltr"
            },
            SupportedLanguage.BENGALI: {
                "name": "Bengali",
                "native_name": "বাংলা",
                "direction": "ltr"
            },
            SupportedLanguage.GUJARATI: {
                "name": "Gujarati",
                "native_name": "ગુજરાતી",
                "direction": "ltr"
            },
            SupportedLanguage.MARATHI: {
                "name": "Marathi",
                "native_name": "मराठी",
                "direction": "ltr"
            },
            SupportedLanguage.PUNJABI: {
                "name": "Punjabi",
                "native_name": "ਪੰਜਾਬੀ",
                "direction": "ltr"
            }
        }
        
        return language_info.get(language_code, language_info[SupportedLanguage.ENGLISH])
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of all supported languages"""
        return [
            {
                "code": lang.value,
                **self.get_language_info(lang.value)
            }
            for lang in SupportedLanguage
        ]
    
    def detect_language_from_request(self, accept_language: str) -> str:
        """Detect preferred language from Accept-Language header"""
        if not accept_language:
            return self.default_language.value
        
        # Parse Accept-Language header
        languages = []
        for lang_range in accept_language.split(','):
            parts = lang_range.strip().split(';')
            lang = parts[0].strip()
            
            # Extract quality factor
            quality = 1.0
            if len(parts) > 1 and parts[1].strip().startswith('q='):
                try:
                    quality = float(parts[1].strip()[2:])
                except ValueError:
                    quality = 1.0
            
            languages.append((lang, quality))
        
        # Sort by quality factor
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Find first supported language
        supported_codes = [lang.value for lang in SupportedLanguage]
        
        for lang_code, _ in languages:
            # Check exact match
            if lang_code in supported_codes:
                return lang_code
            
            # Check language family (e.g., 'en-US' -> 'en')
            lang_family = lang_code.split('-')[0]
            if lang_family in supported_codes:
                return lang_family
        
        return self.default_language.value
    
    def add_translation(self, language_code: str, key: str, value: str):
        """Add or update a translation"""
        if language_code not in self._translations_cache:
            self._translations_cache[language_code] = {}
        
        # Support nested keys
        keys = key.split('.')
        current = self._translations_cache[language_code]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        # Save to file
        self._save_translations(language_code)
    
    def _save_translations(self, language_code: str):
        """Save translations to file"""
        try:
            translation_file = self.translations_dir / f"{language_code}.json"
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self._translations_cache[language_code], 
                    f, 
                    ensure_ascii=False, 
                    indent=2
                )
        except Exception as e:
            logger.error(f"Error saving translations for {language_code}: {str(e)}")

# Global translation manager instance
translation_manager = TranslationManager()

# Convenience functions
def t(key: str, language: str = None, default: str = None, **kwargs) -> str:
    """Shorthand for getting translations"""
    return translation_manager.get_translation(key, language, default, **kwargs)

def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages"""
    return translation_manager.get_supported_languages()

def detect_language(accept_language: str) -> str:
    """Detect language from Accept-Language header"""
    return translation_manager.detect_language_from_request(accept_language)
