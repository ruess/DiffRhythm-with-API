"""
Inference wrapper for DiffRhythm
Wraps the existing infer.py functionality for API use
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path to import DiffRhythm modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torchaudio
from config import settings

logger = logging.getLogger(__name__)


class DiffRhythmInference:
    """Wrapper around DiffRhythm inference functionality"""
    
    def __init__(self):
        """Initialize the inference engine"""
        self.device = self._get_device()
        self.cfm = None
        self.vae = None
        self.tokenizer = None
        self.muq = None
        self.max_frames = None
        
        logger.info(f"Using device: {self.device}")
    
    def _get_device(self) -> str:
        """Determine the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _initialize_models(self, audio_length: int):
        """
        Initialize models if not already initialized
        
        Args:
            audio_length: Audio length in seconds to determine model size
        """
        # Determine max_frames based on audio length
        if audio_length == 95:
            max_frames = 2048
        elif 95 < audio_length <= 285:
            max_frames = 6144
        else:
            raise ValueError(
                f"Invalid audio_length: {audio_length}. "
                "Supported values are exactly 95 or any value between 96 and 285 (inclusive)."
            )
        
        # Initialize models if needed or if max_frames changed
        if self.cfm is None or self.max_frames != max_frames:
            logger.info(f"Initializing models with max_frames={max_frames}")
            
            # Import DiffRhythm modules
            from infer.infer_utils import prepare_model
            
            self.max_frames = max_frames
            self.cfm, self.tokenizer, self.muq, self.vae = prepare_model(
                max_frames, self.device
            )
            
            logger.info("Models initialized successfully")
    
    def generate(
        self,
        lrc_path: str,
        ref_audio_path: Optional[str] = None,
        ref_prompt: Optional[str] = None,
        audio_length: int = 95,
        output_dir: str = None,
        chunked: bool = True,
        batch_infer_num: int = 1,
    ) -> str:
        """
        Generate music from lyrics
        
        Args:
            lrc_path: Path to lyrics file (.lrc format)
            ref_audio_path: Path to reference audio file (optional)
            ref_prompt: Text prompt for style reference (optional)
            audio_length: Audio length in seconds
            output_dir: Output directory for generated music
            chunked: Use chunked decoding
            batch_infer_num: Number of songs per batch
            
        Returns:
            Path to generated audio file
        """
        try:
            # Initialize models
            self._initialize_models(audio_length)
            
            # Import inference utilities
            from infer.infer_utils import (
                get_lrc_token,
                get_style_prompt,
                get_negative_style_prompt,
                get_reference_latent,
                decode_audio,
            )
            from infer.infer import inference
            from einops import rearrange
            import random
            
            # Load lyrics
            with open(lrc_path, "r", encoding='utf-8') as f:
                lrc = f.read()
            
            # Get LRC tokens
            lrc_prompt, start_time, end_frame, song_duration = get_lrc_token(
                self.max_frames, lrc, self.tokenizer, audio_length, self.device
            )
            
            # Get style prompt
            if ref_audio_path:
                style_prompt = get_style_prompt(self.muq, ref_audio_path)
            else:
                style_prompt = get_style_prompt(self.muq, prompt=ref_prompt)
            
            # Get negative style prompt
            negative_style_prompt = get_negative_style_prompt(self.device)
            
            # Get reference latent (no edit mode)
            latent_prompt, pred_frames = get_reference_latent(
                self.device, self.max_frames, False, None, None, self.vae
            )
            
            # Run inference
            logger.info("Running music generation inference...")
            generated_songs = inference(
                cfm_model=self.cfm,
                vae_model=self.vae,
                cond=latent_prompt,
                text=lrc_prompt,
                duration=end_frame,
                style_prompt=style_prompt,
                negative_style_prompt=negative_style_prompt,
                start_time=start_time,
                pred_frames=pred_frames,
                chunked=chunked,
                batch_infer_num=batch_infer_num,
                song_duration=song_duration
            )
            
            # Select one song from the batch
            generated_song = random.sample(generated_songs, 1)[0]
            
            # Save output
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "output.wav")
            torchaudio.save(output_path, generated_song, sample_rate=44100)
            
            logger.info(f"Music generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error during music generation: {str(e)}")
            raise
    
    def edit(
        self,
        lrc_path: str,
        ref_song_path: str,
        ref_audio_path: Optional[str] = None,
        ref_prompt: Optional[str] = None,
        edit_segments: str = None,
        audio_length: int = 95,
        output_dir: str = None,
        chunked: bool = True,
        batch_infer_num: int = 1,
    ) -> str:
        """
        Edit specific segments of an existing song
        
        Args:
            lrc_path: Path to lyrics file (.lrc format)
            ref_song_path: Path to reference song to edit
            ref_audio_path: Path to reference audio file for style (optional)
            ref_prompt: Text prompt for style reference (optional)
            edit_segments: Edit segments in format: [[start1,end1],...]
            audio_length: Audio length in seconds
            output_dir: Output directory for edited music
            chunked: Use chunked decoding
            batch_infer_num: Number of songs per batch
            
        Returns:
            Path to edited audio file
        """
        try:
            # Initialize models
            self._initialize_models(audio_length)
            
            # Import inference utilities
            from infer.infer_utils import (
                get_lrc_token,
                get_style_prompt,
                get_negative_style_prompt,
                get_reference_latent,
            )
            from infer.infer import inference
            import random
            
            # Load lyrics
            with open(lrc_path, "r", encoding='utf-8') as f:
                lrc = f.read()
            
            # Get LRC tokens
            lrc_prompt, start_time, end_frame, song_duration = get_lrc_token(
                self.max_frames, lrc, self.tokenizer, audio_length, self.device
            )
            
            # Get style prompt
            if ref_audio_path:
                style_prompt = get_style_prompt(self.muq, ref_audio_path)
            else:
                style_prompt = get_style_prompt(self.muq, prompt=ref_prompt)
            
            # Get negative style prompt
            negative_style_prompt = get_negative_style_prompt(self.device)
            
            # Get reference latent (with edit mode)
            latent_prompt, pred_frames = get_reference_latent(
                self.device, self.max_frames, True, edit_segments, ref_song_path, self.vae
            )
            
            # Run inference
            logger.info("Running music editing inference...")
            generated_songs = inference(
                cfm_model=self.cfm,
                vae_model=self.vae,
                cond=latent_prompt,
                text=lrc_prompt,
                duration=end_frame,
                style_prompt=style_prompt,
                negative_style_prompt=negative_style_prompt,
                start_time=start_time,
                pred_frames=pred_frames,
                chunked=chunked,
                batch_infer_num=batch_infer_num,
                song_duration=song_duration
            )
            
            # Select one song from the batch
            generated_song = random.sample(generated_songs, 1)[0]
            
            # Save output
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "output.wav")
            torchaudio.save(output_path, generated_song, sample_rate=44100)
            
            logger.info(f"Music edited successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error during music editing: {str(e)}")
            raise
