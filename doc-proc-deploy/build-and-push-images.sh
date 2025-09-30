#!/bin/bash

# Doc Processing Solution - Build and Push Docker Images to Azure Container Registry
# This script builds Docker images and pushes them to Azure Container Registry

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGISTRY=""
TAG="latest"
BUILD_API="false"
BUILD_WEB="false"
BUILD_WORKER="false"
BUILD_ALL="true"

# Function to show usage
usage() {
    echo "Usage: $0 -r <registry-login-server> [options]"
    echo ""
    echo "Required:"
    echo "  -r, --registry         Azure Container Registry login server"
    echo ""
    echo "Optional:"
    echo "  -t, --tag             Image tag (default: latest)"
    echo "  --api                 Build API app image. If specified, only API image will be built."
    echo "  --web                 Build web app image. If specified, only web image will be built."
    echo "  --worker              Build worker app image. If specified, only worker image will be built."
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -r myregistry.azurecr.io"
    echo "  $0 -r myregistry.azurecr.io -t v1.0.0"
    echo "  $0 -r myregistry.azurecr.io -t v1.0.0 --api --web"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        --api)
             BUILD_API="true"
             BUILD_ALL="false"
            shift 1
            ;;
        --web)
             BUILD_WEB="true"
             BUILD_ALL="false"
            shift 1
            ;;
        --worker)
             BUILD_WORKER="true"
             BUILD_ALL="false"
            shift 1
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [ -z "$REGISTRY" ]; then
    echo -e "${RED}❌ Error: Registry login server is required${NC}"
    usage
fi

echo -e "${BLUE}🚀 Building and pushing Docker images to Azure Container Registry${NC}"
echo -e "${BLUE}Registry: $REGISTRY${NC}"
echo -e "${BLUE}Tag: $TAG${NC}"
echo ""

# Output what will be built
if [ "$BUILD_ALL" = "true" ]; then
    echo -e "${BLUE}⚙️  Building all images (API, Web, Worker)${NC}"
    echo ""
else
    echo -e "${BLUE}⚙️  Building selected images:${NC}"
    [ "$BUILD_API" = "true" ] && echo -e "${BLUE}✔️ API${NC}"
    [ "$BUILD_WEB" = "true" ] && echo -e "${BLUE}✔️ Web${NC}"
    [ "$BUILD_WORKER" = "true" ] && echo -e "${BLUE}✔️ Worker${NC}"
    echo ""
fi

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📁 Moving to Project Root: $PROJECT_ROOT${NC}"
# Change to project root
cd "$PROJECT_ROOT"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️ You are not logged in to Azure. Please login first.${NC}"
    az login
fi

echo ""
echo -e "${YELLOW}📋 Current Azure subscription:${NC}"
az account show --output table

# Login to Azure Container Registry
echo ""
echo -e "${BLUE}🔐 Logging in to Azure Container Registry...${NC}"
az acr login --name "${REGISTRY%%.*}"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to login to Azure Container Registry${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Successfully logged in to ACR${NC}"
echo ""

# Get Resource Group of the ACR
RESOURCE_GROUP=$(az acr show --name "${REGISTRY%%.*}" --query "resourceGroup" -o tsv)


# Function to build and push image
build_and_push() {
    local name=$1
    local dockerfile=$2
    local context=$3
    local full_image_name="$REGISTRY/doc-proc-$name:$TAG"
    
    echo -e "${YELLOW}📦 Building $name...${NC}"
    echo -e "${YELLOW}📁  Using docker file: $dockerfile${NC}"
    echo -e "${YELLOW}📁  Context: $context${NC}"
    echo -e "${YELLOW}🏷️  Tagging image as $full_image_name${NC}"

    if docker buildx build --platform linux/amd64 -t "$full_image_name" -f "$dockerfile" "$context"; then
        echo -e "${GREEN}✅ Successfully built $full_image_name${NC}"
        
        echo -e "${YELLOW}📤 Pushing $name to registry...${NC}"
        if docker push "$full_image_name"; then
            echo -e "${GREEN}✅ Successfully pushed $full_image_name${NC}"
        else
            echo -e "${RED}❌ Failed to push $name${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to build $name${NC}"
        return 1
    fi
    printf -- '-%.0s' {1..100}
    echo ""
    echo ""
}


# Build and push all images
printf '=%.0s' {1..100}
echo ""
echo ""
echo -e "${BLUE}Building and pushing images...${NC}"
echo ""

# Build API
if [ "$BUILD_ALL" = "true" ] || [ "$BUILD_API" = "true" ]; then
    build_and_push "api" "doc-proc-api/Dockerfile" "."
    echo "#" * 50
fi

# Build Web
if [ "$BUILD_ALL" = "true" ] || [ "$BUILD_WEB" = "true" ]; then
    build_and_push "web" "doc-proc-web/Dockerfile" "."
fi

# Build worker
if [ "$BUILD_ALL" = "true" ] || [ "$BUILD_WORKER" = "true" ]; then
    build_and_push "worker" "doc-proc-worker/Dockerfile" "."
fi

echo -e "${GREEN}🎉 Image(s) built and pushed successfully!${NC}"
echo ""
echo ""
echo -e "${BLUE}📊 Pushed Image(s):${NC}"
if [ "$BUILD_ALL" = "true" ] || [ "$BUILD_API" = "true" ]; then
    echo -e "${GREEN}✅ $REGISTRY/doc-proc-api:$TAG${NC}"
fi
if [ "$BUILD_ALL" = "true" ] || [ "$BUILD_WEB" = "true" ]; then
    echo -e "${GREEN}✅ $REGISTRY/doc-proc-web:$TAG${NC}"
fi
if [ "$BUILD_ALL" = "true" ] || [ "$BUILD_WORKER" = "true" ]; then
    echo -e "${GREEN}✅ $REGISTRY/doc-proc-worker:$TAG${NC}"
fi

echo ""
echo ""
echo -e "${BLUE}➡️ Next step: Deploy the applications using the deployment script${NC}"
echo "   ./doc-proc-deploy/deploy-apps.sh -g $RESOURCE_GROUP"
echo ""