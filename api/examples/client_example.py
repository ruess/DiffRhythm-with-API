"""
DiffRhythm API Client Example

This script demonstrates how to use the DiffRhythm API to generate music.
"""
import requests
import time
import sys
from pathlib import Path


class DiffRhythmClient:
    """Simple client for DiffRhythm API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> dict:
        """Check if the API is healthy"""
        response = requests.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()
    
    def generate_music(
        self,
        lyrics_path: str,
        ref_audio_path: str = None,
        ref_prompt: str = None,
        audio_length: int = 95,
        chunked: bool = True,
        batch_infer_num: int = 1
    ) -> str:
        """
        Generate music from lyrics
        
        Args:
            lyrics_path: Path to lyrics file (.lrc)
            ref_audio_path: Path to reference audio (optional)
            ref_prompt: Text prompt for style (optional)
            audio_length: Audio length in seconds
            chunked: Use chunked decoding
            batch_infer_num: Number of songs per batch
            
        Returns:
            Task ID
        """
        files = {'lyrics': open(lyrics_path, 'rb')}
        
        if ref_audio_path:
            files['ref_audio'] = open(ref_audio_path, 'rb')
        
        data = {
            'audio_length': audio_length,
            'chunked': chunked,
            'batch_infer_num': batch_infer_num
        }
        
        if ref_prompt:
            data['ref_prompt'] = ref_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()['task_id']
        finally:
            # Close file handles
            for f in files.values():
                f.close()
    
    def edit_music(
        self,
        lyrics_path: str,
        ref_song_path: str,
        edit_segments: str,
        ref_audio_path: str = None,
        ref_prompt: str = None,
        audio_length: int = 95,
        chunked: bool = True,
        batch_infer_num: int = 1
    ) -> str:
        """
        Edit music segments
        
        Args:
            lyrics_path: Path to lyrics file (.lrc)
            ref_song_path: Path to reference song
            edit_segments: Edit segments string (e.g., "[[-1,25],[50.0,-1]]")
            ref_audio_path: Path to reference audio (optional)
            ref_prompt: Text prompt for style (optional)
            audio_length: Audio length in seconds
            chunked: Use chunked decoding
            batch_infer_num: Number of songs per batch
            
        Returns:
            Task ID
        """
        files = {
            'lyrics': open(lyrics_path, 'rb'),
            'ref_song': open(ref_song_path, 'rb')
        }
        
        if ref_audio_path:
            files['ref_audio'] = open(ref_audio_path, 'rb')
        
        data = {
            'edit_segments': edit_segments,
            'audio_length': audio_length,
            'chunked': chunked,
            'batch_infer_num': batch_infer_num
        }
        
        if ref_prompt:
            data['ref_prompt'] = ref_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/edit",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()['task_id']
        finally:
            # Close file handles
            for f in files.values():
                f.close()
    
    def get_status(self, task_id: str) -> dict:
        """Get task status"""
        response = requests.get(f"{self.base_url}/api/status/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def download_result(self, task_id: str, output_path: str):
        """Download generated music"""
        response = requests.get(f"{self.base_url}/api/download/{task_id}")
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
    
    def delete_task(self, task_id: str):
        """Delete a task"""
        response = requests.delete(f"{self.base_url}/api/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 5,
        timeout: int = 600,
        verbose: bool = True
    ) -> dict:
        """
        Wait for a task to complete
        
        Args:
            task_id: Task ID
            poll_interval: Seconds between status checks
            timeout: Maximum time to wait in seconds
            verbose: Print status updates
            
        Returns:
            Final status dictionary
        """
        start_time = time.time()
        
        while True:
            status = self.get_status(task_id)
            
            if verbose:
                progress = status.get('progress', 0)
                print(f"Status: {status['status']} - Progress: {progress}%")
            
            if status['status'] == 'completed':
                if verbose:
                    print("Task completed successfully!")
                return status
            
            if status['status'] == 'failed':
                error = status.get('error', 'Unknown error')
                raise Exception(f"Task failed: {error}")
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task did not complete within {timeout} seconds")
            
            time.sleep(poll_interval)


def example_generate_with_prompt():
    """Example: Generate music with text prompt"""
    print("\n=== Example 1: Generate Music with Text Prompt ===\n")
    
    client = DiffRhythmClient()
    
    # Check API health
    health = client.health_check()
    print(f"API Status: {health['status']}")
    
    # Start generation
    lyrics_path = "../../infer/example/eg_en.lrc"
    ref_prompt = "folk, acoustic guitar, harmonica, touching"
    
    print(f"Generating music with prompt: '{ref_prompt}'")
    task_id = client.generate_music(
        lyrics_path=lyrics_path,
        ref_prompt=ref_prompt,
        audio_length=95,
        chunked=True
    )
    print(f"Task ID: {task_id}")
    
    # Wait for completion
    print("\nWaiting for task to complete...")
    status = client.wait_for_completion(task_id)
    
    # Download result
    output_path = "output_prompt.wav"
    print(f"\nDownloading result to: {output_path}")
    client.download_result(task_id, output_path)
    print("Done!")
    
    return task_id


def example_generate_with_audio():
    """Example: Generate music with audio reference"""
    print("\n=== Example 2: Generate Music with Audio Reference ===\n")
    
    client = DiffRhythmClient()
    
    # Start generation
    lyrics_path = "../../infer/example/eg_en.lrc"
    ref_audio_path = "../../infer/example/eg_en.mp3"
    
    print(f"Generating music with audio reference: {ref_audio_path}")
    task_id = client.generate_music(
        lyrics_path=lyrics_path,
        ref_audio_path=ref_audio_path,
        audio_length=95,
        chunked=True
    )
    print(f"Task ID: {task_id}")
    
    # Wait for completion
    print("\nWaiting for task to complete...")
    status = client.wait_for_completion(task_id)
    
    # Download result
    output_path = "output_audio.wav"
    print(f"\nDownloading result to: {output_path}")
    client.download_result(task_id, output_path)
    print("Done!")
    
    return task_id


def example_edit_music():
    """Example: Edit music segments"""
    print("\n=== Example 3: Edit Music Segments ===\n")
    
    client = DiffRhythmClient()
    
    # Start editing
    lyrics_path = "../../infer/example/edit_en.lrc"
    ref_song_path = "../../infer/example/edit_en.mp3"
    edit_segments = "[[-1,25],[50.0,-1]]"  # Edit beginning and end
    ref_prompt = "folk, acoustic guitar, harmonica, touching"
    
    print(f"Editing music segments: {edit_segments}")
    task_id = client.edit_music(
        lyrics_path=lyrics_path,
        ref_song_path=ref_song_path,
        edit_segments=edit_segments,
        ref_prompt=ref_prompt,
        audio_length=95,
        chunked=True
    )
    print(f"Task ID: {task_id}")
    
    # Wait for completion
    print("\nWaiting for task to complete...")
    status = client.wait_for_completion(task_id)
    
    # Download result
    output_path = "output_edited.wav"
    print(f"\nDownloading result to: {output_path}")
    client.download_result(task_id, output_path)
    print("Done!")
    
    return task_id


def example_status_polling():
    """Example: Manual status polling"""
    print("\n=== Example 4: Manual Status Polling ===\n")
    
    client = DiffRhythmClient()
    
    # Start generation
    lyrics_path = "../../infer/example/eg_en.lrc"
    ref_prompt = "pop, upbeat, electronic"
    
    task_id = client.generate_music(
        lyrics_path=lyrics_path,
        ref_prompt=ref_prompt,
        audio_length=95
    )
    print(f"Task ID: {task_id}")
    
    # Poll status manually
    print("\nPolling status manually...")
    while True:
        status = client.get_status(task_id)
        print(f"Status: {status['status']}, Progress: {status.get('progress', 0)}%")
        
        if status['status'] in ['completed', 'failed']:
            break
        
        time.sleep(5)
    
    if status['status'] == 'completed':
        print("\nTask completed!")
        client.download_result(task_id, "output_manual.wav")
        print("Result downloaded to: output_manual.wav")
    else:
        print(f"\nTask failed: {status.get('error')}")
    
    return task_id


def example_cleanup():
    """Example: Task cleanup"""
    print("\n=== Example 5: Task Cleanup ===\n")
    
    client = DiffRhythmClient()
    
    # Generate music
    lyrics_path = "../../infer/example/eg_en.lrc"
    task_id = client.generate_music(
        lyrics_path=lyrics_path,
        ref_prompt="ambient, relaxing",
        audio_length=95
    )
    print(f"Task ID: {task_id}")
    
    # Wait and download
    client.wait_for_completion(task_id, verbose=False)
    client.download_result(task_id, "output_cleanup.wav")
    print("Result downloaded")
    
    # Delete task
    print("\nDeleting task...")
    result = client.delete_task(task_id)
    print(result['message'])


if __name__ == "__main__":
    # Check if API is running
    try:
        client = DiffRhythmClient()
        client.health_check()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server.")
        print("Please ensure the API server is running:")
        print("  cd api && python main.py")
        sys.exit(1)
    
    print("DiffRhythm API Client Examples")
    print("=" * 50)
    
    # Run examples
    try:
        # Example 1: Generate with text prompt
        example_generate_with_prompt()
        
        # Example 2: Generate with audio reference
        # example_generate_with_audio()
        
        # Example 3: Edit music
        # example_edit_music()
        
        # Example 4: Manual status polling
        # example_status_polling()
        
        # Example 5: Cleanup
        # example_cleanup()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
