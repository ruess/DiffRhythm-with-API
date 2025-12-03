#!/bin/bash

# CapRover Deployment Script for DiffRhythm
# This script helps automate the deployment process

set -e

echo "======================================"
echo "DiffRhythm CapRover Deployment Script"
echo "======================================"
echo ""

# Check if caprover CLI is installed
if ! command -v caprover &> /dev/null; then
    echo "❌ CapRover CLI is not installed!"
    echo "Please install it first: npm install -g caprover"
    exit 1
fi

echo "✅ CapRover CLI found"
echo ""

# Check if required files exist
if [ ! -f "captain-definition" ]; then
    echo "❌ captain-definition file not found!"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found!"
    exit 1
fi

echo "✅ Required files found"
echo ""

# Get app name
read -p "Enter your CapRover app name (e.g., diffrhythm-api): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "❌ App name is required!"
    exit 1
fi

echo ""
echo "📦 Preparing deployment for: $APP_NAME"
echo ""

# Check if git repo is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    read -p "Do you want to continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Deployment cancelled. Please commit your changes first."
        exit 0
    fi
fi

echo ""
echo "🚀 Starting deployment..."
echo ""

# Deploy using CapRover CLI
caprover deploy -a "$APP_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ Deployment successful!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Configure environment variables in CapRover dashboard"
    echo "2. Set up persistent storage for /app/api_storage"
    echo "3. Increase memory limit to at least 8GB"
    echo "4. Enable HTTPS for your app"
    echo ""
    echo "Health check: https://$APP_NAME.your-domain.com/api/health"
    echo "API docs: https://$APP_NAME.your-domain.com/docs"
    echo ""
    echo "See CAPROVER_DEPLOYMENT.md for detailed instructions"
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the logs with: caprover logs -a $APP_NAME"
    exit 1
fi
