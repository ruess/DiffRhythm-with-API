# CapRover Deployment Guide for DiffRhythm

This guide will help you deploy the DiffRhythm API on your CapRover server.

## Prerequisites

1. **CapRover Server**: A running CapRover instance
2. **CapRover CLI**: Install with `npm install -g caprover`
3. **Git**: Repository access
4. **System Requirements**: 
   - Minimum 8GB RAM (16GB+ recommended)
   - GPU support (CUDA) recommended for better performance
   - 20GB+ disk space for models and dependencies

## Quick Deployment Steps

### 1. Prepare Your Project

The project is already containerized with:
- `Dockerfile` - Optimized for CapRover with API server
- `captain-definition` - CapRover configuration file
- `.dockerignore` - Excludes unnecessary files

### 2. Login to CapRover

```bash
caprover login
```

Follow the prompts to enter:
- CapRover server URL
- Password
- Save as default (optional)

### 3. Create a New App

In CapRover dashboard:
1. Go to "Apps" section
2. Click "One-Click Apps/Databases"
3. Or manually create a new app:
   - Click "Create New App"
   - Enter app name (e.g., `diffrhythm-api`)
   - Click "Create New App"

### 4. Deploy from Git Repository

#### Option A: Deploy from GitHub

1. Push your code to GitHub if not already there
2. In CapRover dashboard, go to your app
3. Under "Deployment" tab:
   - Method: "Deploy from Github/Bitbucket/Gitlab"
   - Repository: `https://github.com/your-username/DiffRhythm.git`
   - Branch: `main` (or your branch name)
   - Username: Your GitHub username
   - Password/Token: GitHub personal access token
4. Click "Save & Update"

#### Option B: Deploy from CLI

From your project root directory:

```bash
caprover deploy
```

When prompted:
- Select your CapRover server
- Enter app name: `diffrhythm-api`
- Select branch to deploy

### 5. Configure App Settings

In CapRover dashboard, navigate to your app:

#### HTTP Settings
- Enable HTTPS (recommended)
- Force HTTPS (optional)
- Container HTTP Port: `80`

#### Environment Variables

Add the following environment variables:

```bash
API_HOST=0.0.0.0
API_PORT=80
DEBUG=False
CORS_ORIGINS=*
PYTHONUNBUFFERED=1
```

**Optional Environment Variables:**
```bash
# If you want to restrict CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# For debugging (not recommended in production)
DEBUG=True
```

#### App Configs

1. **Persistent Data**:
   - Add a persistent directory for model storage and generated files
   - Path in App: `/app/api_storage`
   - Label: `api-storage`

2. **Memory Settings**:
   - Increase container memory limit to at least 8GB
   - Recommended: 16GB or more

### 6. Advanced Configuration (Optional)

#### Custom Dockerfile Build Arguments

If you need to customize the build, you can modify the `captain-definition` file:

```json
{
  "schemaVersion": 2,
  "dockerfilePath": "./Dockerfile",
  "dockerfileLines": [
    "FROM python:3.10-slim",
    "..."
  ]
}
```

#### GPU Support

If your CapRover server has GPU support:

1. Ensure NVIDIA Docker runtime is installed on the host
2. In CapRover dashboard, under "App Configs":
   - Add custom Docker parameters
   - Add: `--gpus all` or `--gpus device=0`

3. Update Dockerfile to use CUDA base image (optional):
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
```

#### Pre-download Models

To speed up first startup, you can pre-download models:

1. SSH into your CapRover server
2. Access the container:
```bash
docker exec -it $(docker ps | grep diffrhythm | awk '{print $1}') bash
```

3. Download models manually or run a test inference

### 7. Verify Deployment

#### Check Health

Visit: `https://your-app-name.your-domain.com/api/health`

Expected response:
```json
{
  "status": "healthy",
  "message": "DiffRhythm API is running",
  "version": "1.0.0"
}
```

#### Access API Documentation

Visit: `https://your-app-name.your-domain.com/docs`

This will show the interactive Swagger UI with all available endpoints.

#### Test Generation

```bash
curl -X POST "https://your-app-name.your-domain.com/api/generate" \
  -F "lyrics=@path/to/lyrics.lrc" \
  -F "ref_prompt=folk, acoustic guitar, harmonica, touching" \
  -F "audio_length=95" \
  -F "chunked=true"
```

## Monitoring and Maintenance

### View Logs

In CapRover dashboard:
1. Go to your app
2. Click "App Logs" tab
3. View real-time logs

Or via CLI:
```bash
caprover logs --app diffrhythm-api
```

### Resource Monitoring

Monitor:
- CPU usage
- Memory usage (should stay under limit)
- Disk space (especially `/app/api_storage`)
- Network traffic

### Automatic Cleanup

The API automatically cleans up task files after 24 hours. Monitor disk usage to ensure this is working correctly.

### Manual Cleanup

If needed, SSH into the container:
```bash
docker exec -it $(docker ps | grep diffrhythm | awk '{print $1}') bash
cd /app/api_storage
# Remove old task directories
find . -type d -mtime +1 -exec rm -rf {} +
```

## Scaling Considerations

### Vertical Scaling
- Increase container resources (CPU, RAM, GPU)
- Add more workers to uvicorn (modify CMD in Dockerfile)

### Horizontal Scaling
- Deploy multiple instances
- Use a load balancer (CapRover supports this)
- Implement a shared storage solution (e.g., NFS, S3)
- Use a task queue (e.g., Celery with Redis)

## Troubleshooting

### Container Won't Start

1. Check logs: `caprover logs --app diffrhythm-api`
2. Common issues:
   - Out of memory (increase container memory)
   - Port conflicts (ensure port 80 is used)
   - Missing dependencies (rebuild image)

### API Responds Slowly

1. Check if models are loaded (first request is slow)
2. Verify GPU is being used (if available)
3. Increase container resources
4. Enable chunked decoding: `chunked=true`

### CUDA/GPU Errors

1. Verify GPU is available on host
2. Check NVIDIA Docker runtime installation
3. Ensure proper GPU passthrough in Docker parameters
4. PyTorch may default to CPU if CUDA unavailable

### Permission Errors

1. Check persistent storage permissions
2. Ensure `/app/api_storage` is writable
3. May need to run container with specific user/group

### Build Failures

1. Check Dockerfile syntax
2. Verify all required files are present
3. Check .dockerignore isn't excluding required files
4. Increase build timeout in CapRover settings

## Security Best Practices

1. **HTTPS**: Always enable HTTPS in production
2. **CORS**: Restrict `CORS_ORIGINS` to specific domains
3. **Rate Limiting**: Implement rate limiting (use nginx or API gateway)
4. **Authentication**: Add authentication layer if needed
5. **Firewall**: Restrict access to CapRover dashboard
6. **Updates**: Keep dependencies updated regularly

## Backup and Recovery

### Backup Strategy

1. **Persistent Data**: Backup `/app/api_storage`
2. **Configuration**: Export CapRover app config
3. **Database**: If using external DB, backup regularly

### Recovery

1. Redeploy from Git repository
2. Restore persistent data from backup
3. Reconfigure environment variables
4. Verify health endpoint

## Performance Optimization

### For Production

1. **Disable Debug Mode**: `DEBUG=False`
2. **Use Production ASGI Server**: Already configured with uvicorn
3. **Enable Compression**: Add nginx compression in CapRover
4. **Cache Models**: Use persistent storage for model cache
5. **Monitor Performance**: Set up monitoring (Prometheus, Grafana)

### Memory Optimization

- Use `chunked=true` for inference
- Limit concurrent requests
- Adjust `batch_infer_num` based on available memory
- Consider implementing request queue

## Support and Resources

- **DiffRhythm Docs**: See `api/README.md`
- **CapRover Docs**: https://caprover.com/docs/
- **API Documentation**: `https://your-app.domain.com/docs`
- **Issue Tracker**: Report issues on GitHub

## Example Environment Setup

Complete `.env` file for production:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=80
DEBUG=False

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com

# Python Configuration
PYTHONUNBUFFERED=1

# eSpeak Configuration
PHONEMIZER_ESPEAK_LIBRARY=/usr/lib/x86_64-linux-gnu/libespeak-ng.so.1
PHONEMIZER_ESPEAK_PATH=/usr/bin
```

## Updating the Application

To update your deployed app:

```bash
# Pull latest changes
git pull origin main

# Deploy update
caprover deploy
```

Or configure auto-deployment from GitHub in CapRover dashboard.

---

**Need Help?** Check the API documentation at `/docs` endpoint or review the logs for detailed error messages.
