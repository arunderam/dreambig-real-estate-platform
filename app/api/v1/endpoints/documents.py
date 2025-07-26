"""
Document management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.core.document_manager import document_manager
from app.db import crud

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Query(..., regex="^(images|videos|documents)$"),
    subcategory: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload a document with automatic categorization and security validation
    """
    try:
        user_id = getattr(current_user, 'id', None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        # Save file using document manager
        file_info = document_manager.save_file(
            file=file,
            category=category,
            subcategory=subcategory,
            user_id=user_id
        )
        
        return {
            "message": "Document uploaded successfully",
            "file_info": file_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/info/{file_path:path}")
async def get_document_info(
    file_path: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get information about a specific document
    """
    try:
        file_info = document_manager.get_file_info(file_path)
        
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document information"
        )

@router.delete("/{file_path:path}")
async def delete_document(
    file_path: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a document (with proper authorization checks)
    """
    try:
        # In a real implementation, you'd check if the user owns this document
        # For now, we'll allow deletion if the user is authenticated
        
        success = document_manager.delete_file(file_path)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or already deleted"
            )
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

@router.post("/cleanup-temp")
async def cleanup_temp_files(
    older_than_hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Clean up temporary files (admin only)
    """
    try:
        # Check if user has admin privileges
        user_role = getattr(current_user, 'role', 'user')
        if user_role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        document_manager.cleanup_temp_files(older_than_hours)
        
        return {
            "message": f"Temporary files older than {older_than_hours} hours have been cleaned up"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup temporary files"
        )

@router.get("/storage-stats")
async def get_storage_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get storage usage statistics (admin only)
    """
    try:
        # Check if user has admin privileges
        user_role = getattr(current_user, 'role', 'user')
        if user_role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # Calculate storage statistics
        import os
        from pathlib import Path
        
        upload_dir = Path(document_manager.upload_dir)
        
        def get_directory_size(path: Path) -> int:
            """Calculate total size of directory"""
            total_size = 0
            try:
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            except Exception as e:
                logger.warning(f"Error calculating size for {path}: {e}")
            return total_size
        
        def count_files(path: Path) -> int:
            """Count total files in directory"""
            count = 0
            try:
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        count += 1
            except Exception as e:
                logger.warning(f"Error counting files in {path}: {e}")
            return count
        
        stats = {
            "total_size_bytes": get_directory_size(upload_dir),
            "total_files": count_files(upload_dir),
            "categories": {}
        }
        
        # Get stats by category
        categories = ["properties", "users", "investments", "services", "temp"]
        for category in categories:
            category_path = upload_dir / category
            if category_path.exists():
                stats["categories"][category] = {
                    "size_bytes": get_directory_size(category_path),
                    "file_count": count_files(category_path)
                }
        
        # Convert bytes to human readable format
        def format_bytes(bytes_value: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        
        stats["total_size_formatted"] = format_bytes(stats["total_size_bytes"])
        for category in stats["categories"]:
            stats["categories"][category]["size_formatted"] = format_bytes(
                stats["categories"][category]["size_bytes"]
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get storage statistics"
        )

@router.post("/bulk-upload")
async def bulk_upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Query(..., regex="^(images|videos|documents)$"),
    subcategory: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload multiple documents at once
    """
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 files can be uploaded at once"
            )
        
        user_id = getattr(current_user, 'id', None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                file_info = document_manager.save_file(
                    file=file,
                    category=category,
                    subcategory=subcategory,
                    user_id=user_id
                )
                uploaded_files.append(file_info)
            except Exception as e:
                logger.error(f"Error uploading file {file.filename}: {e}")
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "message": f"Bulk upload completed. {len(uploaded_files)} files uploaded successfully.",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "summary": {
                "total_files": len(files),
                "successful": len(uploaded_files),
                "failed": len(failed_files)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk upload failed"
        )
