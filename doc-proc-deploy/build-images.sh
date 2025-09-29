#!/bin/bash

# Doc Processing Solution - Docker Build Script
# This script builds all Docker images for the document processing solution

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default image tag
TAG=${1:-"latest"}

echo -e "${BLUE}🚀 Building Doc Processing Solution Docker Images${NC}"
echo -e "${BLUE}Project Root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}Image Tag: $TAG${NC}"
echo ""

# Function to build image
build_image() {
    local name=$1
    local dockerfile=$2
    local context=$3
    
    echo -e "${YELLOW}📦 Building $name...${NC}"
    
    if docker build -t "doc-proc-$name:$TAG" -f "$dockerfile" "$context"; then
        echo -e "${GREEN}✅ Successfully built doc-proc-$name:$TAG${NC}"
    else
        echo -e "${RED}❌ Failed to build doc-proc-$name${NC}"
        return 1
    fi
    echo ""
}

# Change to project root
cd "$PROJECT_ROOT"

# Build all images
echo -e "${BLUE}Building all components...${NC}"
echo ""

# Build backend
build_image "backend" "Dockerfile.backend" "."

# Build worker
build_image "worker" "Dockerfile.worker" "."

# Build frontend
build_image "frontend" "Dockerfile.frontend" "."

echo -e "${GREEN}🎉 All images built successfully!${NC}"
echo ""
echo -e "${BLUE}Available images:${NC}"
docker images | grep "doc-proc-" | grep "$TAG"

echo ""
echo -e "${BLUE}To run the services, use: ./doc-proc-deploy/run-containers.sh${NC}"