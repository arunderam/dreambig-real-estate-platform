from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.utils.i18n import (
    translation_manager, 
    SupportedLanguage, 
    t, 
    get_supported_languages,
    detect_language
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic schemas for i18n

class LanguageInfo(BaseModel):
    code: str
    name: str
    native_name: str
    direction: str

class TranslationRequest(BaseModel):
    keys: List[str] = Field(..., description="List of translation keys to fetch")
    language: Optional[str] = Field(None, description="Language code (defaults to user preference)")

class TranslationResponse(BaseModel):
    language: str
    translations: Dict[str, str]

class LanguagePreferenceRequest(BaseModel):
    language: str = Field(..., description="Preferred language code")

# Language Management Endpoints

@router.get("/languages", response_model=List[LanguageInfo])
async def get_available_languages():
    """Get list of all supported languages"""
    try:
        languages = get_supported_languages()
        return [
            LanguageInfo(
                code=lang["code"],
                name=lang["name"],
                native_name=lang["native_name"],
                direction=lang["direction"]
            )
            for lang in languages
        ]
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported languages"
        )

@router.get("/detect-language")
async def detect_user_language(
    accept_language: Optional[str] = Header(None, alias="Accept-Language")
):
    """Detect user's preferred language from browser headers"""
    try:
        detected_language = detect_language(accept_language or "")
        language_info = translation_manager.get_language_info(detected_language)
        
        return {
            "detected_language": detected_language,
            "language_info": language_info,
            "confidence": "high" if accept_language else "low"
        }
    except Exception as e:
        logger.error(f"Error detecting language: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect language"
        )

# Translation Endpoints

@router.post("/translations", response_model=TranslationResponse)
async def get_translations(
    request: TranslationRequest,
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get translations for specified keys"""
    try:
        # Determine language to use
        language = request.language
        if not language:
            # Try to get user's preferred language (would be stored in user profile)
            # For now, detect from headers
            language = detect_language(accept_language or "")
        
        # Validate language
        supported_codes = [lang.value for lang in SupportedLanguage]
        if language not in supported_codes:
            language = SupportedLanguage.ENGLISH.value
        
        # Get translations for all requested keys
        translations = {}
        for key in request.keys:
            translations[key] = t(key, language)
        
        return TranslationResponse(
            language=language,
            translations=translations
        )
        
    except Exception as e:
        logger.error(f"Error getting translations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve translations"
        )

@router.get("/translations/{language}")
async def get_all_translations_for_language(
    language: str,
    section: Optional[str] = None
):
    """Get all translations for a specific language"""
    try:
        # Validate language
        supported_codes = [lang.value for lang in SupportedLanguage]
        if language not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language: {language}"
            )
        
        # Get all translations for the language
        all_translations = translation_manager._translations_cache.get(language, {})
        
        # Filter by section if specified
        if section:
            translations = all_translations.get(section, {})
        else:
            translations = all_translations
        
        return {
            "language": language,
            "section": section,
            "translations": translations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting translations for language {language}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve translations"
        )

# User Language Preferences

@router.post("/user/language-preference")
async def set_user_language_preference(
    preference: LanguagePreferenceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Set user's language preference"""
    try:
        # Validate language
        supported_codes = [lang.value for lang in SupportedLanguage]
        if preference.language not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language: {preference.language}"
            )
        
        # In a real implementation, you would update the user's profile in the database
        # For now, we'll just return success
        # user = db.query(User).filter(User.id == current_user.id).first()
        # user.preferred_language = preference.language
        # db.commit()
        
        return {
            "message": "Language preference updated successfully",
            "language": preference.language,
            "language_info": translation_manager.get_language_info(preference.language)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting language preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update language preference"
        )

@router.get("/user/language-preference")
async def get_user_language_preference(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user's language preference"""
    try:
        # In a real implementation, you would get this from the user's profile
        # For now, return default
        # user = db.query(User).filter(User.id == current_user.id).first()
        # preferred_language = user.preferred_language or SupportedLanguage.ENGLISH.value
        
        preferred_language = SupportedLanguage.ENGLISH.value
        
        return {
            "language": preferred_language,
            "language_info": translation_manager.get_language_info(preferred_language)
        }
        
    except Exception as e:
        logger.error(f"Error getting language preference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve language preference"
        )

# Utility Endpoints

@router.get("/translate")
async def translate_text(
    key: str,
    language: Optional[str] = None,
    default: Optional[str] = None,
    accept_language: Optional[str] = Header(None, alias="Accept-Language")
):
    """Translate a single key (utility endpoint)"""
    try:
        # Determine language
        if not language:
            language = detect_language(accept_language or "")
        
        # Get translation
        translation = t(key, language, default)
        
        return {
            "key": key,
            "language": language,
            "translation": translation,
            "language_info": translation_manager.get_language_info(language)
        }
        
    except Exception as e:
        logger.error(f"Error translating key {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to translate text"
        )

@router.get("/sections")
async def get_translation_sections(language: Optional[str] = None):
    """Get available translation sections"""
    try:
        if not language:
            language = SupportedLanguage.ENGLISH.value
        
        # Validate language
        supported_codes = [lang.value for lang in SupportedLanguage]
        if language not in supported_codes:
            language = SupportedLanguage.ENGLISH.value
        
        # Get sections (top-level keys in translations)
        translations = translation_manager._translations_cache.get(language, {})
        sections = list(translations.keys())
        
        return {
            "language": language,
            "sections": sections
        }
        
    except Exception as e:
        logger.error(f"Error getting translation sections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve translation sections"
        )

# Admin Endpoints (for managing translations)

@router.post("/admin/translations")
async def add_translation(
    language: str,
    key: str,
    value: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Add or update a translation (admin only)"""
    try:
        # In a real implementation, check if user is admin
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate language
        supported_codes = [lang.value for lang in SupportedLanguage]
        if language not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language: {language}"
            )
        
        # Add translation
        translation_manager.add_translation(language, key, value)
        
        return {
            "message": "Translation added successfully",
            "language": language,
            "key": key,
            "value": value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add translation"
        )

@router.get("/admin/missing-translations")
async def get_missing_translations(
    base_language: str = SupportedLanguage.ENGLISH.value,
    target_language: Optional[str] = None
):
    """Get missing translations for a language compared to base language"""
    try:
        # Validate languages
        supported_codes = [lang.value for lang in SupportedLanguage]
        if base_language not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported base language: {base_language}"
            )
        
        if target_language and target_language not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target language: {target_language}"
            )
        
        base_translations = translation_manager._translations_cache.get(base_language, {})
        
        if target_language:
            target_translations = translation_manager._translations_cache.get(target_language, {})
            missing_keys = []
            
            def find_missing_keys(base_dict, target_dict, prefix=""):
                for key, value in base_dict.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        target_sub = target_dict.get(key, {}) if isinstance(target_dict.get(key), dict) else {}
                        find_missing_keys(value, target_sub, current_key)
                    else:
                        if key not in target_dict:
                            missing_keys.append(current_key)
            
            find_missing_keys(base_translations, target_translations)
            
            return {
                "base_language": base_language,
                "target_language": target_language,
                "missing_keys": missing_keys,
                "total_missing": len(missing_keys)
            }
        else:
            # Return missing translations for all languages
            result = {}
            for lang in supported_codes:
                if lang != base_language:
                    target_translations = translation_manager._translations_cache.get(lang, {})
                    missing_keys = []
                    
                    def find_missing_keys(base_dict, target_dict, prefix=""):
                        for key, value in base_dict.items():
                            current_key = f"{prefix}.{key}" if prefix else key
                            if isinstance(value, dict):
                                target_sub = target_dict.get(key, {}) if isinstance(target_dict.get(key), dict) else {}
                                find_missing_keys(value, target_sub, current_key)
                            else:
                                if key not in target_dict:
                                    missing_keys.append(current_key)
                    
                    find_missing_keys(base_translations, target_translations)
                    result[lang] = {
                        "missing_keys": missing_keys,
                        "total_missing": len(missing_keys)
                    }
            
            return {
                "base_language": base_language,
                "languages": result
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting missing translations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve missing translations"
        )
