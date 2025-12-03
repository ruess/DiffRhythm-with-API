# DiffRhythm CapRover Deployment - Setup Complete ✅

## What's Been Done

Your DiffRhythm project has been successfully containerized and prepared for CapRover deployment!

### Files Created

1. **`Dockerfile`** - Production-ready container image
   - Based on Python 3.10-slim
   - Includes all system dependencies (espeak-ng, ffmpeg)
   - Installs all Python requirements
   - Configured for port 80 (CapRover default)
   - Includes health check endpoint
   - Runs the FastAPI server with uvicorn

2. **`captain-definition`** - CapRover configuration
   - Points to the Dockerfile
   - Uses schema version 2

3. **`.dockerignore`** - Optimizes build
   - Excludes unnecessary files
   - Reduces image size
   - Speeds up deployment

4. **`CAPROVER_DEPLOYMENT.md`** - Complete deployment guide
   - Step-by-step instructions
   - Configuration details
   - Troubleshooting tips
   - Security best practices
   - Scaling strategies

5. **`deploy-caprover.sh`** - Automated deployment script
   - Validates requirements
   - Deploys to CapRover
   - Provides post-deployment instructions

## Quick Start

### Prerequisites
```bash
# Install CapRover CLI
npm install -g caprover

# Login to your CapRover server
caprover login
```

### Deploy Now

**Option 1: Using the script (recommended)**
```bash
./deploy-caprover.sh
```

**Option 2: Manual deployment**
```bash
caprover deploy -a diffrhythm-api
```

## Essential Configuration

After deployment, configure these settings in CapRover dashboard:

### 1. Environment Variables
```bash
API_HOST=0.0.0.0
API_PORT=80
DEBUG=False
CORS_ORIGINS=*
PYTHONUNBUFFERED=1
```

### 2. Container Settings
- **HTTP Port**: 80
- **Memory**: Minimum 8GB (16GB+ recommended)
- **Persistent Storage**: Mount `/app/api_storage`

### 3. Enable HTTPS
- Enable HTTPS in CapRover dashboard
- Force HTTPS (recommended)

## Test Your Deployment

Once deployed, verify:

1. **Health Check**
   ```bash
   curl https://your-app.your-domain.com/api/health
   ```

2. **API Documentation**
   - Visit: `https://your-app.your-domain.com/docs`

3. **Generate Music**
   ```bash
   curl -X POST "https://your-app.your-domain.com/api/generate" \
     -F "lyrics=@lyrics.lrc" \
     -F "ref_prompt=folk, acoustic guitar" \
     -F "audio_length=95" \
     -F "chunked=true"
   ```

## Key Features

✅ **Production Ready** - Optimized for production use
✅ **Auto Health Checks** - Built-in health monitoring
✅ **Efficient Build** - Optimized Docker layers
✅ **CORS Support** - Configurable cross-origin requests
✅ **Persistent Storage** - Data survives restarts
✅ **Auto Cleanup** - Tasks cleaned after 24 hours
✅ **Interactive Docs** - Swagger UI at `/docs`

## Important Notes

### System Requirements
- **RAM**: 8GB minimum (16GB+ recommended for better performance)
- **Storage**: 20GB+ for models and dependencies
- **GPU**: Optional but recommended (requires CUDA runtime on host)

### First Request
The first API request will be slower as models load into memory. Subsequent requests will be faster.

### Memory Settings
For systems with 8GB RAM, always use `chunked=true` in requests to reduce VRAM usage.

### Persistent Data
Configure persistent storage for `/app/api_storage` to preserve:
- Generated audio files
- Task metadata
- Uploaded reference files

## Next Steps

1. **Deploy**: Run `./deploy-caprover.sh` or `caprover deploy`
2. **Configure**: Set environment variables in CapRover
3. **Test**: Verify health endpoint and run test generation
4. **Monitor**: Check logs and resource usage
5. **Scale**: Adjust resources based on usage

## Documentation

- **Deployment Guide**: See `CAPROVER_DEPLOYMENT.md` for detailed instructions
- **API Documentation**: See `api/README.md` for API usage
- **Interactive Docs**: Visit `/docs` endpoint after deployment

## Support

For issues or questions:
- Check logs: `caprover logs -a diffrhythm-api`
- Review `CAPROVER_DEPLOYMENT.md` troubleshooting section
- Test locally with: `docker build -t diffrhythm . && docker run -p 8000:80 diffrhythm`

---

**Ready to deploy!** 🚀

Run `./deploy-caprover.sh` to get started.
