"""
DiffRhythm API Server
FastAPI-based REST API for DiffRhythm music generation
"""
import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import shutil
from pathlib import Path

from models import (
    GenerateRequest,
    GenerateResponse,
    EditRequest,
    TaskStatusResponse,
    HealthResponse,
)
from tasks import generate_music_task, edit_music_task, get_task_status, cleanup_task
from storage import StorageManager
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DiffRhythm API",
    description="REST API for DiffRhythm music generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage manager
storage = StorageManager(settings.STORAGE_PATH)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "DiffRhythm API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="DiffRhythm API is running",
        version="1.0.0"
    )


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_music(
    background_tasks: BackgroundTasks,
    lyrics: UploadFile = File(..., description="Lyrics file (.lrc format)"),
    ref_audio: Optional[UploadFile] = File(None, description="Reference audio file (optional if ref_prompt provided)"),
    ref_prompt: Optional[str] = Form(None, description="Text style prompt (optional if ref_audio provided)"),
    audio_length: int = Form(95, description="Audio length in seconds (95 or 96-285)"),
    chunked: bool = Form(True, description="Use chunked decoding (recommended for 8GB VRAM)"),
    batch_infer_num: int = Form(1, description="Number of songs per batch"),
):
    """
    Generate music from lyrics with style reference
    
    Either ref_audio OR ref_prompt must be provided, but not both.
    """
    try:
        # Validate inputs
        if not ref_audio and not ref_prompt:
            raise HTTPException(
                status_code=400,
                detail="Either ref_audio or ref_prompt must be provided"
            )
        
        if ref_audio and ref_prompt:
            raise HTTPException(
                status_code=400,
                detail="Only one of ref_audio or ref_prompt should be provided"
            )
        
        if audio_length < 95 or audio_length > 285:
            raise HTTPException(
                status_code=400,
                detail="Audio length must be 95 or between 96-285 seconds"
            )
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        logger.info(f"Creating new generation task: {task_id}")
        
        # Create task directory
        task_dir = storage.create_task_directory(task_id)
        
        # Save lyrics file
        lyrics_path = storage.save_uploaded_file(lyrics, task_id, "lyrics.lrc")
        
        # Save reference audio if provided
        ref_audio_path = None
        if ref_audio:
            ref_audio_path = storage.save_uploaded_file(ref_audio, task_id, ref_audio.filename)
        
        # Create task parameters
        task_params = {
            "task_id": task_id,
            "lyrics_path": lyrics_path,
            "ref_audio_path": ref_audio_path,
            "ref_prompt": ref_prompt,
            "audio_length": audio_length,
            "chunked": chunked,
            "batch_infer_num": batch_infer_num,
            "output_dir": str(task_dir / "output"),
        }
        
        # Start background task
        background_tasks.add_task(generate_music_task, task_params)
        
        # Schedule cleanup after 24 hours
        background_tasks.add_task(cleanup_task, task_id, delay=86400)
        
        logger.info(f"Task {task_id} queued successfully")
        
        return GenerateResponse(
            task_id=task_id,
            status="queued",
            message="Music generation task queued successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating generation task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/edit", response_model=GenerateResponse)
async def edit_music(
    background_tasks: BackgroundTasks,
    lyrics: UploadFile = File(..., description="Lyrics file (.lrc format)"),
    ref_song: UploadFile = File(..., description="Reference song to edit"),
    ref_audio: Optional[UploadFile] = File(None, description="Reference audio for style (optional if ref_prompt provided)"),
    ref_prompt: Optional[str] = Form(None, description="Text style prompt (optional if ref_audio provided)"),
    edit_segments: str = Form(..., description="Edit segments in format: [[start1,end1],...]"),
    audio_length: int = Form(95, description="Audio length in seconds"),
    chunked: bool = Form(True, description="Use chunked decoding"),
    batch_infer_num: int = Form(1, description="Number of songs per batch"),
):
    """
    Edit specific segments of an existing song
    
    edit_segments format: [[start1,end1],[start2,end2],...]
    Use -1 for audio start/end (e.g., [[-1,25],[50.0,-1]])
    """
    try:
        # Validate inputs
        if not ref_audio and not ref_prompt:
            raise HTTPException(
                status_code=400,
                detail="Either ref_audio or ref_prompt must be provided"
            )
        
        if ref_audio and ref_prompt:
            raise HTTPException(
                status_code=400,
                detail="Only one of ref_audio or ref_prompt should be provided"
            )
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        logger.info(f"Creating new edit task: {task_id}")
        
        # Create task directory
        task_dir = storage.create_task_directory(task_id)
        
        # Save files
        lyrics_path = storage.save_uploaded_file(lyrics, task_id, "lyrics.lrc")
        ref_song_path = storage.save_uploaded_file(ref_song, task_id, ref_song.filename)
        
        ref_audio_path = None
        if ref_audio:
            ref_audio_path = storage.save_uploaded_file(ref_audio, task_id, ref_audio.filename)
        
        # Create task parameters
        task_params = {
            "task_id": task_id,
            "lyrics_path": lyrics_path,
            "ref_song_path": ref_song_path,
            "ref_audio_path": ref_audio_path,
            "ref_prompt": ref_prompt,
            "edit_segments": edit_segments,
            "audio_length": audio_length,
            "chunked": chunked,
            "batch_infer_num": batch_infer_num,
            "output_dir": str(task_dir / "output"),
        }
        
        # Start background task
        background_tasks.add_task(edit_music_task, task_params)
        
        # Schedule cleanup after 24 hours
        background_tasks.add_task(cleanup_task, task_id, delay=86400)
        
        logger.info(f"Edit task {task_id} queued successfully")
        
        return GenerateResponse(
            task_id=task_id,
            status="queued",
            message="Music editing task queued successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating edit task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str):
    """Get the status of a generation task"""
    try:
        status = get_task_status(task_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/download/{task_id}")
async def download_result(task_id: str):
    """Download the generated audio file"""
    try:
        status = get_task_status(task_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Task is not completed yet. Current status: {status.status}"
            )
        
        if not status.output_path:
            raise HTTPException(status_code=404, detail="Output file not found")
        
        output_path = Path(status.output_path)
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")
        
        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=f"{task_id}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and its associated files"""
    try:
        storage.cleanup_task(task_id)
        return {"message": f"Task {task_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
