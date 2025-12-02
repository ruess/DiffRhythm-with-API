"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class GenerateRequest(BaseModel):
    """Request model for music generation"""
    lyrics: str = Field(..., description="Lyrics content in LRC format")
    ref_audio_path: Optional[str] = Field(None, description="Path to reference audio file")
    ref_prompt: Optional[str] = Field(None, description="Text prompt for style reference")
    audio_length: int = Field(95, ge=95, le=285, description="Audio length in seconds")
    chunked: bool = Field(True, description="Use chunked decoding")
    batch_infer_num: int = Field(1, ge=1, description="Number of songs per batch")

    @validator('ref_audio_path', 'ref_prompt')
    def validate_reference(cls, v, values):
        """Ensure either ref_audio_path or ref_prompt is provided, but not both"""
        if 'ref_audio_path' in values:
            ref_audio = values.get('ref_audio_path')
            if ref_audio and v:
                raise ValueError("Only one of ref_audio_path or ref_prompt should be provided")
            if not ref_audio and not v:
                raise ValueError("Either ref_audio_path or ref_prompt must be provided")
        return v


class EditRequest(BaseModel):
    """Request model for music editing"""
    lyrics: str = Field(..., description="Lyrics content in LRC format")
    ref_song_path: str = Field(..., description="Path to reference song to edit")
    ref_audio_path: Optional[str] = Field(None, description="Path to reference audio file for style")
    ref_prompt: Optional[str] = Field(None, description="Text prompt for style reference")
    edit_segments: str = Field(..., description="Edit segments: [[start1,end1],...]")
    audio_length: int = Field(95, ge=95, le=285, description="Audio length in seconds")
    chunked: bool = Field(True, description="Use chunked decoding")
    batch_infer_num: int = Field(1, ge=1, description="Number of songs per batch")


class GenerateResponse(BaseModel):
    """Response model for generation/edit requests"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status: queued, processing, completed, failed")
    message: str = Field(..., description="Status message")


class TaskStatusResponse(BaseModel):
    """Response model for task status queries"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status: queued, processing, completed, failed")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message or error details")
    output_path: Optional[str] = Field(None, description="Path to generated audio file")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")
