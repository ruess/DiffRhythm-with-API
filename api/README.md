# DiffRhythm API

REST API wrapper for DiffRhythm music generation. This API allows you to generate and edit music programmatically using HTTP requests.

## Features

- **Generate Music**: Create full-length songs from lyrics with style references
- **Edit Music**: Modify specific segments of existing songs
- **Async Processing**: Background task processing with status tracking
- **File Management**: Automatic file storage and cleanup
- **Multiple Formats**: Support for audio files and text prompts as style references

## Installation

1. Install DiffRhythm dependencies:
```bash
pip install -r ../requirements.txt
```

2. Install API dependencies:
```bash
pip install -r requirements-api.txt
```

3. Ensure espeak-ng is installed (see main DiffRhythm README for OS-specific instructions)

## Quick Start

### Starting the API Server

```bash
cd api
python main.py
```

The API will start on `http://localhost:8000` by default.

### Configuration

Set environment variables to customize the API:

```bash
export API_HOST=0.0.0.0
export API_PORT=8000
export DEBUG=False
export CORS_ORIGINS=*
```

Or create a `.env` file in the `api` directory:
```
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
CORS_ORIGINS=*
```

## API Endpoints

### Health Check

**GET** `/api/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "DiffRhythm API is running",
  "version": "1.0.0"
}
```

### Generate Music

**POST** `/api/generate`

Generate music from lyrics with a style reference.

**Parameters:**
- `lyrics` (file, required): Lyrics file in .lrc format
- `ref_audio` (file, optional): Reference audio file for style
- `ref_prompt` (string, optional): Text prompt for style (e.g., "folk, acoustic guitar, harmonica, touching")
- `audio_length` (int, default: 95): Audio length in seconds (95 or 96-285)
- `chunked` (bool, default: true): Use chunked decoding (recommended for 8GB VRAM)
- `batch_infer_num` (int, default: 1): Number of songs per batch

**Note:** Either `ref_audio` OR `ref_prompt` must be provided, but not both.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Music generation task queued successfully"
}
```

### Edit Music

**POST** `/api/edit`

Edit specific segments of an existing song.

**Parameters:**
- `lyrics` (file, required): Lyrics file in .lrc format
- `ref_song` (file, required): Reference song to edit
- `ref_audio` (file, optional): Reference audio for style
- `ref_prompt` (string, optional): Text prompt for style
- `edit_segments` (string, required): Edit segments in format: `[[start1,end1],[start2,end2]]`
- `audio_length` (int, default: 95): Audio length in seconds
- `chunked` (bool, default: true): Use chunked decoding
- `batch_infer_num` (int, default: 1): Number of songs per batch

**Edit Segments Format:**
- Time segments in seconds
- Use `-1` for audio start/end
- Example: `[[-1,25],[50.0,-1]]` edits beginning to 25s and 50s to end

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Music editing task queued successfully"
}
```

### Get Task Status

**GET** `/api/status/{task_id}`

Check the status of a generation or edit task.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": null,
  "output_path": "/path/to/output.wav",
  "created_at": "2025-03-01T12:00:00",
  "completed_at": "2025-03-01T12:05:00",
  "error": null
}
```

**Status values:**
- `queued`: Task is waiting to be processed
- `processing`: Task is currently being processed
- `completed`: Task completed successfully
- `failed`: Task failed with an error

### Download Result

**GET** `/api/download/{task_id}`

Download the generated audio file.

**Response:** Audio file (WAV format)

### Delete Task

**DELETE** `/api/tasks/{task_id}`

Delete a task and its associated files.

**Response:**
```json
{
  "message": "Task 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

## Usage Examples

### Using cURL

#### Generate music with text prompt:
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "lyrics=@path/to/lyrics.lrc" \
  -F "ref_prompt=folk, acoustic guitar, harmonica, touching" \
  -F "audio_length=95" \
  -F "chunked=true"
```

#### Generate music with audio reference:
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "lyrics=@path/to/lyrics.lrc" \
  -F "ref_audio=@path/to/reference.mp3" \
  -F "audio_length=95"
```

#### Check task status:
```bash
curl "http://localhost:8000/api/status/{task_id}"
```

#### Download result:
```bash
curl "http://localhost:8000/api/download/{task_id}" -o output.wav
```

### Using Python

See `examples/client_example.py` for a complete Python client implementation.

```python
import requests

# Generate music
with open("lyrics.lrc", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/generate",
        files={"lyrics": f},
        data={
            "ref_prompt": "folk, acoustic guitar, harmonica, touching",
            "audio_length": 95,
            "chunked": True
        }
    )

task_id = response.json()["task_id"]

# Check status
status = requests.get(f"http://localhost:8000/api/status/{task_id}").json()

# Download result when complete
if status["status"] == "completed":
    audio = requests.get(f"http://localhost:8000/api/download/{task_id}")
    with open("output.wav", "wb") as f:
        f.write(audio.content)
```

## Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can test the API directly from your browser.

## Task Management

### Automatic Cleanup

Tasks are automatically cleaned up after 24 hours. You can also manually delete tasks using the DELETE endpoint.

### Storage Location

Task files are stored in the `api_storage` directory at the project root. Each task has its own subdirectory containing:
- `input/`: Uploaded files (lyrics, reference audio)
- `output/`: Generated audio files
- `metadata.txt`: Task metadata and status

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Task not found
- `500`: Internal server error

Error responses include a `detail` field with the error message:
```json
{
  "detail": "Either ref_audio or ref_prompt must be provided"
}
```

## Performance Considerations

- **VRAM Requirements**: DiffRhythm-base requires minimum 8GB VRAM. Use `chunked=true` for 8GB systems.
- **First Request**: The first generation request will be slower as models are loaded into memory.
- **Concurrent Requests**: The API processes requests sequentially. For production use, consider using a task queue like Celery.
- **File Cleanup**: Old tasks are automatically cleaned up after 24 hours to save disk space.

## Troubleshooting

### Port Already in Use
If port 8000 is in use, change it:
```bash
export API_PORT=8001
python main.py
```

### CUDA/GPU Issues
If you encounter GPU memory errors, ensure `chunked=true` and reduce `batch_infer_num`.

### Module Import Errors
Ensure you're running from the `api` directory and the parent DiffRhythm directory is accessible.

## Development

### Running in Debug Mode
```bash
export DEBUG=True
python main.py
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- Verbose logging

### Running with Uvicorn Directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## License

This API wrapper is released under the same Apache 2.0 License as DiffRhythm.
