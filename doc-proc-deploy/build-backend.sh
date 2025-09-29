#!/bin/bash

# Build and Deploy Backend Script
# This script builds the backend Docker image using ACR and deploys it to Container Apps

set -e

# Configuration
RESOURCE_GROUP_NAME="${RESOURCE_GROUP_NAME:-rg-docproc-dev}"
REGISTRY_NAME="${REGISTRY_NAME}"
IMAGE_NAME="doc-proc-backend"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BACKEND_APP_NAME="${BACKEND_APP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for colored output
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if required parameters are set
if [ -z "$REGISTRY_NAME" ]; then
    error "REGISTRY_NAME environment variable is required"
fi

if [ -z "$BACKEND_APP_NAME" ]; then
    error "BACKEND_APP_NAME environment variable is required"
fi

# Check if we're in the right directory
if [ ! -d "../doc-proc-ui/backend-app" ]; then
    error "Backend app directory not found. Please run this script from doc-proc-deploy directory"
fi

# Check if ACR exists
log "Checking if Container Registry exists..."
if ! az acr show --name "$REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" >/dev/null 2>&1; then
    error "Container Registry '$REGISTRY_NAME' not found in resource group '$RESOURCE_GROUP_NAME'"
fi

# Build image using ACR
log "Building Docker image using Azure Container Registry..."
az acr build \
    --registry "$REGISTRY_NAME" \
    --image "${IMAGE_NAME}:${IMAGE_TAG}" \
    --file ../doc-proc-ui/backend-app/Dockerfile \
    ../doc-proc-ui/backend-app

if [ $? -eq 0 ]; then
    log "Image built successfully: ${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"
else
    error "Failed to build Docker image"
fi

# Update Container App with new image
log "Updating Container App with new image..."
FULL_IMAGE_NAME="${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

az containerapp update \
    --name "$BACKEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --image "$FULL_IMAGE_NAME"

if [ $? -eq 0 ]; then
    log "Container App updated successfully"
    
    # Get the application URL
    APP_URL=$(az containerapp show \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv)
    
    if [ -n "$APP_URL" ]; then
        log "Backend application is available at: https://$APP_URL"
        log "Health check endpoint: https://$APP_URL/health"
    fi
else
    error "Failed to update Container App"
fi

log "Deployment completed successfully!"