# DiffRhythm API Quick Start Guide

Get up and running with the DiffRhythm API in minutes!

## Installation

1. **Install dependencies:**
```bash
# From the project root
pip install -r requirements.txt
pip install -r api/requirements-api.txt
```

2. **Ensure espeak-ng is installed:**
   - **Ubuntu/Debian:** `sudo apt-get install espeak-ng`
   - **CentOS/Fedora:** `sudo yum install espeak-ng`
   - **macOS:** `brew install espeak-ng`
   - **Windows:** Download from [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases)

## Start the API Server

```bash
cd api
python main.py
```

The server will start at `http://localhost:8000`

## Your First Request

### Using cURL

```bash
# Generate music with a text prompt
curl -X POST "http://localhost:8000/api/generate" \
  -F "lyrics=@../infer/example/eg_en.lrc" \
  -F "ref_prompt=folk, acoustic guitar, harmonica, touching" \
  -F "audio_length=95" \
  -F "chunked=true"
```

This will return a task ID:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Music generation task queued successfully"
}
```

### Check Status

```bash
curl "http://localhost:8000/api/status/YOUR_TASK_ID"
```

### Download Result

```bash
curl "http://localhost:8000/api/download/YOUR_TASK_ID" -o output.wav
```

## Using Python

```python
import requests
import time

# 1. Submit generation request
with open("../infer/example/eg_en.lrc", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/generate",
        files={"lyrics": f},
        data={
            "ref_prompt": "folk, acoustic guitar, harmonica",
            "audio_length": 95,
            "chunked": True
        }
    )

task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# 2. Wait for completion
while True:
    status = requests.get(f"http://localhost:8000/api/status/{task_id}").json()
    print(f"Status: {status['status']}, Progress: {status.get('progress', 0)}%")
    
    if status["status"] == "completed":
        break
    
    time.sleep(5)

# 3. Download result
audio = requests.get(f"http://localhost:8000/api/download/{task_id}")
with open("output.wav", "wb") as f:
    f.write(audio.content)

print("Music generated successfully!")
```

## Using the Example Client

We provide a complete Python client with examples:

```bash
cd api/examples
python client_example.py
```

This will run a complete example that generates music and downloads the result.

## Interactive Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide interactive documentation where you can test the API directly from your browser!

## Common Use Cases

### Generate with Text Prompt (No Audio Reference)

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "lyrics=@lyrics.lrc" \
  -F "ref_prompt=jazz, piano, saxophone, smooth" \
  -F "audio_length=95"
```

### Generate with Audio Reference

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "lyrics=@lyrics.lrc" \
  -F "ref_audio=@reference.mp3" \
  -F "audio_length=95"
```

### Edit Music Segments

```bash
curl -X POST "http://localhost:8000/api/edit" \
  -F "lyrics=@lyrics.lrc" \
  -F "ref_song=@original.mp3" \
  -F "ref_prompt=upbeat, electronic" \
  -F "edit_segments=[[-1,25],[50,-1]]" \
  -F "audio_length=95"
```

This edits the beginning (to 25s) and end (from 50s) of the song.

## Tips

- **First request is slower** - Models need to load into memory
- **Use `chunked=true`** - Required for systems with 8GB VRAM
- **Monitor with status endpoint** - Check progress regularly
- **Tasks auto-cleanup** - After 24 hours, or delete manually
- **Interactive docs** - Use `/docs` for easy testing

## Troubleshooting

### "Cannot connect to API server"
Make sure the server is running:
```bash
cd api
python main.py
```

### "Port already in use"
Change the port:
```bash
export API_PORT=8001
python main.py
```

### "CUDA out of memory"
Ensure `chunked=true` in your requests:
```bash
-F "chunked=true"
```

## Next Steps

- Read the full [API Documentation](README.md)
- Explore the [Python client examples](examples/client_example.py)
- Check out the [interactive docs](http://localhost:8000/docs) for detailed endpoint information

## Need Help?

- Check the main [DiffRhythm README](../Readme.md)
- Review [API Documentation](README.md)
- See [example code](examples/client_example.py)

Happy music generation! 🎵
