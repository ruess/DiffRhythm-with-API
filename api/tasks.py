"""
Background task handlers for music generation and editing
"""
import os
import sys
import logging
import time
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

from storage import StorageManager
from config import settings
from models import TaskStatusResponse
from inference import DiffRhythmInference

logger = logging.getLogger(__name__)

# Initialize storage manager
storage = StorageManager(settings.STORAGE_PATH)

# Initialize inference engine (lazy loading)
_inference_engine = None


def get_inference_engine():
    """Get or initialize the inference engine"""
    global _inference_engine
    if _inference_engine is None:
        logger.info("Initializing DiffRhythm inference engine...")
        _inference_engine = DiffRhythmInference()
        logger.info("Inference engine initialized successfully")
    return _inference_engine


def generate_music_task(task_params: dict):
    """
    Background task for music generation
    
    Args:
        task_params: Dictionary containing task parameters
    """
    task_id = task_params["task_id"]
    
    try:
        logger.info(f"Starting generation task: {task_id}")
        storage.update_task_status(task_id, "processing", progress=0)
        
        # Get inference engine
        inference = get_inference_engine()
        
        # Update progress
        storage.update_task_status(task_id, "processing", progress=10)
        
        # Run inference
        output_path = inference.generate(
            lrc_path=task_params["lyrics_path"],
            ref_audio_path=task_params.get("ref_audio_path"),
            ref_prompt=task_params.get("ref_prompt"),
            audio_length=task_params["audio_length"],
            output_dir=task_params["output_dir"],
            chunked=task_params.get("chunked", True),
            batch_infer_num=task_params.get("batch_infer_num", 1),
        )
        
        # Update status to completed
        storage.update_task_status(
            task_id,
            "completed",
            progress=100,
            output_path=output_path,
            completed_at=datetime.now().isoformat()
        )
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        error_msg = f"Error in generation task: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        logger.error(traceback.format_exc())
        
        storage.update_task_status(
            task_id,
            "failed",
            error=error_msg,
            completed_at=datetime.now().isoformat()
        )


def edit_music_task(task_params: dict):
    """
    Background task for music editing
    
    Args:
        task_params: Dictionary containing task parameters
    """
    task_id = task_params["task_id"]
    
    try:
        logger.info(f"Starting edit task: {task_id}")
        storage.update_task_status(task_id, "processing", progress=0)
        
        # Get inference engine
        inference = get_inference_engine()
        
        # Update progress
        storage.update_task_status(task_id, "processing", progress=10)
        
        # Run inference with edit mode
        output_path = inference.edit(
            lrc_path=task_params["lyrics_path"],
            ref_song_path=task_params["ref_song_path"],
            ref_audio_path=task_params.get("ref_audio_path"),
            ref_prompt=task_params.get("ref_prompt"),
            edit_segments=task_params["edit_segments"],
            audio_length=task_params["audio_length"],
            output_dir=task_params["output_dir"],
            chunked=task_params.get("chunked", True),
            batch_infer_num=task_params.get("batch_infer_num", 1),
        )
        
        # Update status to completed
        storage.update_task_status(
            task_id,
            "completed",
            progress=100,
            output_path=output_path,
            completed_at=datetime.now().isoformat()
        )
        
        logger.info(f"Edit task {task_id} completed successfully")
        
    except Exception as e:
        error_msg = f"Error in edit task: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        logger.error(traceback.format_exc())
        
        storage.update_task_status(
            task_id,
            "failed",
            error=error_msg,
            completed_at=datetime.now().isoformat()
        )


def get_task_status(task_id: str) -> Optional[TaskStatusResponse]:
    """
    Get the status of a task
    
    Args:
        task_id: Unique task identifier
        
    Returns:
        TaskStatusResponse or None if task not found
    """
    metadata = storage.get_task_metadata(task_id)
    
    if metadata is None:
        return None
    
    return TaskStatusResponse(
        task_id=task_id,
        status=metadata.get("status", "unknown"),
        progress=int(metadata.get("progress", 0)) if "progress" in metadata else None,
        message=metadata.get("message"),
        output_path=metadata.get("output_path"),
        created_at=metadata.get("created_at"),
        completed_at=metadata.get("completed_at"),
        error=metadata.get("error")
    )


def cleanup_task(task_id: str, delay: int = 0):
    """
    Cleanup a task after a delay
    
    Args:
        task_id: Unique task identifier
        delay: Delay in seconds before cleanup
    """
    if delay > 0:
        logger.info(f"Scheduling cleanup for task {task_id} in {delay} seconds")
        time.sleep(delay)
    
    try:
        storage.cleanup_task(task_id)
        logger.info(f"Cleaned up task: {task_id}")
    except Exception as e:
        logger.error(f"Error cleaning up task {task_id}: {str(e)}")
