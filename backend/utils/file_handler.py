"""
File Management Utilities
Handles file cleanup, directory management, and validation
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileHandler:
    """Professional file management with safety checks"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize file handler
        
        Args:
            base_dir: Base directory for operations
        """
        self.base_dir = base_dir or Path.cwd()
    
    def ensure_directories(self, directories: Optional[List[str]] = None):
        """
        Create necessary directories if they don't exist
        
        Args:
            directories: List of directory paths to create
        """
        default_dirs = ["uploads", "outputs", "temp"]
        dirs_to_create = directories or default_dirs
        
        created = []
        for dir_name in dirs_to_create:
            dir_path = self.base_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(dir_name)
                logger.info(f"📁 Created directory: {dir_name}")
        
        if created:
            logger.info(f"✅ Initialized {len(created)} directories")
        else:
            logger.info("✅ All directories already exist")
    
    def cleanup_temp_files(
        self,
        directory: str,
        pattern: str = "*",
        older_than_hours: Optional[int] = None
    ):
        """
        Remove temporary files from directory
        
        Args:
            directory: Directory to clean
            pattern: File pattern to match (e.g., "*.wav")
            older_than_hours: Only delete files older than X hours
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                logger.warning(f"Directory not found: {directory}")
                return
            
            files_deleted = 0
            space_freed = 0
            
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    # Check age if specified
                    if older_than_hours:
                        file_age = datetime.now() - datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        )
                        if file_age < timedelta(hours=older_than_hours):
                            continue
                    
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    files_deleted += 1
                    space_freed += file_size
            
            if files_deleted > 0:
                space_mb = space_freed / (1024 * 1024)
                logger.info(f"🧹 Cleaned up {files_deleted} files ({space_mb:.1f} MB)")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def cleanup_old_jobs(self, directory: str, days_old: int = 7):
        """
        Remove job files older than specified days
        
        Args:
            directory: Directory containing job files
            days_old: Delete files older than this many days
        """
        self.cleanup_temp_files(
            directory,
            pattern="*",
            older_than_hours=days_old * 24
        )
    
    def get_directory_size(self, directory: str) -> float:
        """
        Calculate total size of directory
        
        Args:
            directory: Directory path
        
        Returns:
            Size in MB
        """
        try:
            dir_path = Path(directory)
            total_size = sum(
                f.stat().st_size
                for f in dir_path.rglob('*')
                if f.is_file()
            )
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.error(f"Failed to calculate directory size: {e}")
            return 0.0
    
    def validate_file(
        self,
        file_path: str,
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: Optional[float] = None
    ) -> bool:
        """
        Validate file exists and meets requirements
        
        Args:
            file_path: Path to file
            allowed_extensions: List of allowed extensions (e.g., ['.mp4', '.avi'])
            max_size_mb: Maximum file size in MB
        
        Returns:
            True if valid, raises exception otherwise
        """
        path = Path(file_path)
        
        # Check existence
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check extension
        if allowed_extensions:
            if path.suffix.lower() not in allowed_extensions:
                raise ValueError(
                    f"Invalid file type: {path.suffix}. "
                    f"Allowed: {', '.join(allowed_extensions)}"
                )
        
        # Check size
        if max_size_mb:
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                raise ValueError(
                    f"File too large: {file_size_mb:.1f} MB. "
                    f"Maximum: {max_size_mb} MB"
                )
        
        return True
    
    def safe_delete(self, file_path: str) -> bool:
        """
        Safely delete file with error handling
        
        Args:
            file_path: Path to file to delete
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug(f"Deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return False

# Global instance
_file_handler = None

def get_file_handler() -> FileHandler:
    """Get or create global file handler"""
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler()
    return _file_handler

def ensure_directories(directories: Optional[List[str]] = None):
    """Convenience function for directory creation"""
    handler = get_file_handler()
    handler.ensure_directories(directories)

def cleanup_temp_files(directory: str):
    """Convenience function for cleanup"""
    handler = get_file_handler()
    handler.cleanup_temp_files(directory)
