# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for eSpeak and other requirements
RUN apt-get update && apt-get install -y \
    git \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for eSpeak
ENV PHONEMIZER_ESPEAK_LIBRARY=/usr/lib/x86_64-linux-gnu/libespeak-ng.so.1
ENV PHONEMIZER_ESPEAK_PATH=/usr/bin

# Copy the entire project
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r api/requirements-api.txt

# Create necessary directories
RUN mkdir -p /app/api_storage && \
    mkdir -p /app/infer/example/output

# Set environment variables for API
ENV API_HOST=0.0.0.0
ENV API_PORT=80
ENV DEBUG=False
ENV CORS_ORIGINS=*
ENV PYTHONUNBUFFERED=1

# Expose port 80 (CapRover default)
EXPOSE 80

# Change to API directory and start the server
WORKDIR /app/api

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:80/api/health')" || exit 1

# Start the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
