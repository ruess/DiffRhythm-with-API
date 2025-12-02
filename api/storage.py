"""
File storage management for DiffRhythm API
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from fastapi import UploadFile

from config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage for tasks"""
    
    def __init__(self, base_path: Path):
        """
        Initialize storage manager
        
        Args:
            base_path: Base directory for storing task files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage manager initialized at: {self.base_path}")
    
    def get_task_directory(self, task_id: str) -> Path:
        """Get the directory for a specific task"""
        return self.base_path / task_id
    
    def create_task_directory(self, task_id: str) -> Path:
        """
        Create a directory for a new task
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Path to the created directory
        """
        task_dir = self.get_task_directory(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (task_dir / "input").mkdir(exist_ok=True)
        (task_dir / "output").mkdir(exist_ok=True)
        
        # Create metadata file
        metadata = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
        metadata_path = task_dir / "metadata.txt"
        with open(metadata_path, "w") as f:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Created task directory: {task_dir}")
        return task_dir
    
    def save_uploaded_file(
        self, 
        upload_file: UploadFile, 
        task_id: str, 
        filename: Optional[str] = None
    ) -> str:
        """
        Save an uploaded file to the task directory
        
        Args:
            upload_file: The uploaded file
            task_id: Unique task identifier
            filename: Optional custom filename (uses upload_file.filename if not provided)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            filename = upload_file.filename
        
        task_dir = self.get_task_directory(task_id)
        input_dir = task_dir / "input"
        file_path = input_dir / filename
        
        # Save file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)
        
        logger.info(f"Saved uploaded file: {file_path}")
        return str(file_path)
    
    def get_output_file(self, task_id: str, filename: str = "output.wav") -> Optional[Path]:
        """
        Get the path to an output file
        
        Args:
            task_id: Unique task identifier
            filename: Output filename
            
        Returns:
            Path to the output file if it exists, None otherwise
        """
        output_path = self.get_task_directory(task_id) / "output" / filename
        if output_path.exists():
            return output_path
        return None
    
    def cleanup_task(self, task_id: str):
        """
        Delete all files associated with a task
        
        Args:
            task_id: Unique task identifier
        """
        task_dir = self.get_task_directory(task_id)
        if task_dir.exists():
            shutil.rmtree(task_dir)
            logger.info(f"Cleaned up task directory: {task_dir}")
    
    def cleanup_old_tasks(self, max_age_seconds: int = None):
        """
        Clean up tasks older than the specified age
        
        Args:
            max_age_seconds: Maximum age in seconds (uses settings default if not provided)
        """
        if max_age_seconds is None:
            max_age_seconds = settings.MAX_TASK_AGE_SECONDS
        
        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
        
        for task_dir in self.base_path.iterdir():
            if not task_dir.is_dir():
                continue
            
            metadata_path = task_dir / "metadata.txt"
            if not metadata_path.exists():
                continue
            
            # Read metadata to get creation time
            try:
                with open(metadata_path, "r") as f:
                    for line in f:
                        if line.startswith("created_at:"):
                            created_at_str = line.split(":", 1)[1].strip()
                            created_at = datetime.fromisoformat(created_at_str)
                            
                            if created_at < cutoff_time:
                                logger.info(f"Cleaning up old task: {task_dir.name}")
                                shutil.rmtree(task_dir)
                            break
            except Exception as e:
                logger.error(f"Error checking task age: {e}")
    
    def update_task_status(self, task_id: str, status: str, **kwargs):
        """
        Update task status in metadata file
        
        Args:
            task_id: Unique task identifier
            status: New status
            **kwargs: Additional metadata fields to update
        """
        task_dir = self.get_task_directory(task_id)
        metadata_path = task_dir / "metadata.txt"
        
        if not metadata_path.exists():
            logger.warning(f"Metadata file not found for task: {task_id}")
            return
        
        # Read existing metadata
        metadata = {}
        with open(metadata_path, "r") as f:
            for line in f:
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
        
        # Update status and other fields
        metadata["status"] = status
        metadata["updated_at"] = datetime.now().isoformat()
        
        for key, value in kwargs.items():
            metadata[key] = str(value)
        
        # Write updated metadata
        with open(metadata_path, "w") as f:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Updated task {task_id} status to: {status}")
    
    def get_task_metadata(self, task_id: str) -> Optional[dict]:
        """
        Get task metadata
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Dictionary of metadata or None if not found
        """
        task_dir = self.get_task_directory(task_id)
        metadata_path = task_dir / "metadata.txt"
        
        if not metadata_path.exists():
            return None
        
        metadata = {}
        with open(metadata_path, "r") as f:
            for line in f:
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
        
        return metadata
