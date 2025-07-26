"""
Enhanced document management system for DreamBig
"""
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from PIL import Image
import magic
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.db import models, crud
from app.utils.validation import validate_file_upload
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentManager:
    """Enhanced document management with security and organization"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR or "app/static/uploads")
        self.max_file_size = settings.MAX_FILE_SIZE or 10 * 1024 * 1024  # 10MB
        self.allowed_image_extensions = (settings.ALLOWED_IMAGE_EXTENSIONS or "jpg,jpeg,png,gif,webp").split(",")
        self.allowed_video_extensions = (settings.ALLOWED_VIDEO_EXTENSIONS or "mp4,avi,mov,wmv").split(",")
        self.allowed_document_extensions = ["pdf", "doc", "docx", "txt", "rtf"]
        
        # Create upload directories
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary upload directories"""
        directories = [
            "properties/images",
            "properties/videos",
            "properties/documents",
            "users/kyc",
            "users/profile",
            "investments/documents",
            "services/documents",
            "temp"
        ]
        
        for directory in directories:
            dir_path = self.upload_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def generate_secure_filename(self, original_filename: str, user_id: int = None) -> str:
        """Generate secure filename with hash"""
        file_ext = Path(original_filename).suffix.lower()
        
        # Create unique identifier
        unique_id = str(uuid.uuid4())
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Add user context if provided
        context = f"{user_id}_{timestamp}" if user_id else timestamp
        
        # Create hash for additional security
        hash_input = f"{unique_id}_{context}_{original_filename}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        
        return f"{unique_id}_{file_hash}{file_ext}"
    
    def validate_file(self, file: UploadFile, allowed_types: List[str]) -> Tuple[bool, str]:
        """Validate uploaded file"""
        try:
            # Check file size
            if hasattr(file, 'size') and file.size > self.max_file_size:
                return False, f"File size exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB"
            
            # Check file extension
            if not file.filename:
                return False, "No filename provided"
            
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
            if file_ext not in allowed_types:
                return False, f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_types)}"
            
            # Read file content for validation
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            # Check actual file type using python-magic
            try:
                file_type = magic.from_buffer(content, mime=True)
                expected_types = {
                    'jpg': ['image/jpeg'],
                    'jpeg': ['image/jpeg'],
                    'png': ['image/png'],
                    'gif': ['image/gif'],
                    'webp': ['image/webp'],
                    'pdf': ['application/pdf'],
                    'mp4': ['video/mp4'],
                    'avi': ['video/x-msvideo'],
                    'mov': ['video/quicktime'],
                    'wmv': ['video/x-ms-wmv']
                }
                
                if file_ext in expected_types:
                    if file_type not in expected_types[file_ext]:
                        return False, f"File content doesn't match extension. Expected: {expected_types[file_ext]}, Got: {file_type}"
            
            except Exception as e:
                logger.warning(f"Could not validate file type: {e}")
            
            return True, "File is valid"
            
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return False, f"File validation error: {str(e)}"
    
    def save_file(
        self, 
        file: UploadFile, 
        category: str, 
        subcategory: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Save uploaded file with metadata"""
        try:
            # Determine allowed file types based on category
            allowed_types = []
            if category == "images":
                allowed_types = self.allowed_image_extensions
            elif category == "videos":
                allowed_types = self.allowed_video_extensions
            elif category == "documents":
                allowed_types = self.allowed_document_extensions
            else:
                allowed_types = self.allowed_image_extensions + self.allowed_video_extensions + self.allowed_document_extensions
            
            # Validate file
            is_valid, message = self.validate_file(file, allowed_types)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            
            # Generate secure filename
            secure_filename = self.generate_secure_filename(file.filename, user_id)
            
            # Determine file path
            if subcategory:
                file_path = self.upload_dir / category / subcategory / secure_filename
            else:
                file_path = self.upload_dir / category / secure_filename
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            # Generate file metadata
            file_info = {
                "original_filename": file.filename,
                "secure_filename": secure_filename,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.upload_dir)),
                "url": f"/static/uploads/{file_path.relative_to(self.upload_dir)}".replace("\\", "/"),
                "file_size": len(content),
                "mime_type": file.content_type or mimetypes.guess_type(file.filename)[0],
                "category": category,
                "subcategory": subcategory,
                "uploaded_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Process image files for thumbnails
            if category == "images":
                try:
                    thumbnail_info = self.create_thumbnail(file_path)
                    file_info.update(thumbnail_info)
                except Exception as e:
                    logger.warning(f"Could not create thumbnail for {secure_filename}: {e}")
            
            logger.info(f"File saved successfully: {secure_filename}")
            return file_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    def create_thumbnail(self, image_path: Path, sizes: List[Tuple[int, int]] = None) -> Dict[str, Any]:
        """Create thumbnails for images"""
        if sizes is None:
            sizes = [(150, 150), (300, 300), (600, 400)]  # small, medium, large
        
        thumbnails = {}
        
        try:
            with Image.open(image_path) as img:
                # Get original dimensions
                original_width, original_height = img.size
                
                for i, (width, height) in enumerate(sizes):
                    # Calculate aspect ratio preserving dimensions
                    img_copy = img.copy()
                    img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    # Generate thumbnail filename
                    thumb_filename = f"{image_path.stem}_thumb_{width}x{height}{image_path.suffix}"
                    thumb_path = image_path.parent / "thumbnails" / thumb_filename
                    
                    # Create thumbnails directory
                    thumb_path.parent.mkdir(exist_ok=True)
                    
                    # Save thumbnail
                    img_copy.save(thumb_path, optimize=True, quality=85)
                    
                    size_name = ["small", "medium", "large"][i] if i < 3 else f"custom_{i}"
                    thumbnails[f"thumbnail_{size_name}"] = {
                        "url": f"/static/uploads/{thumb_path.relative_to(self.upload_dir)}".replace("\\", "/"),
                        "width": img_copy.width,
                        "height": img_copy.height
                    }
                
                thumbnails["original_dimensions"] = {
                    "width": original_width,
                    "height": original_height
                }
                
        except Exception as e:
            logger.error(f"Error creating thumbnails: {e}")
        
        return thumbnails
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file and its thumbnails"""
        try:
            full_path = self.upload_dir / file_path
            
            if full_path.exists():
                # Delete main file
                full_path.unlink()
                
                # Delete thumbnails if they exist
                if "images" in file_path:
                    thumb_dir = full_path.parent / "thumbnails"
                    if thumb_dir.exists():
                        for thumb_file in thumb_dir.glob(f"{full_path.stem}_thumb_*{full_path.suffix}"):
                            thumb_file.unlink()
                
                logger.info(f"File deleted successfully: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            full_path = self.upload_dir / file_path
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                "file_path": file_path,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "mime_type": mimetypes.guess_type(str(full_path))[0],
                "exists": True
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            temp_dir = self.upload_dir / "temp"
            if not temp_dir.exists():
                return
            
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            cleaned_count = 0
            
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

# Global document manager instance
document_manager = DocumentManager()

# Convenience functions
def save_property_image(file: UploadFile, property_id: int, user_id: int) -> Dict[str, Any]:
    """Save property image"""
    return document_manager.save_file(file, "properties", "images", user_id)

def save_property_video(file: UploadFile, property_id: int, user_id: int) -> Dict[str, Any]:
    """Save property video"""
    return document_manager.save_file(file, "properties", "videos", user_id)

def save_property_document(file: UploadFile, property_id: int, user_id: int) -> Dict[str, Any]:
    """Save property document"""
    return document_manager.save_file(file, "properties", "documents", user_id)

def save_kyc_document(file: UploadFile, user_id: int) -> Dict[str, Any]:
    """Save KYC document"""
    return document_manager.save_file(file, "users", "kyc", user_id)

def save_investment_document(file: UploadFile, investment_id: int, user_id: int) -> Dict[str, Any]:
    """Save investment document"""
    return document_manager.save_file(file, "investments", "documents", user_id)
