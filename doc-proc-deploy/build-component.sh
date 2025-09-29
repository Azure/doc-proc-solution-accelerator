#!/bin/bash

# Doc Processing Solution - Individual Component Build Script
# This script builds a specific component Docker image

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

# Usage function
usage() {
    echo "Usage: $0 <component> [tag]"
    echo ""
    echo "Components:"
    echo "  backend  - Build backend API image"
    echo "  worker   - Build worker image"
    echo "  frontend - Build frontend UI image"
    echo ""
    echo "Options:"
    echo "  tag      - Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 backend"
    echo "  $0 worker dev"
    exit 1
}

# Check parameters
if [ $# -lt 1 ]; then
    usage
fi

COMPONENT=$1
TAG=${2:-"latest"}

echo -e "${BLUE}🚀 Building Doc Processing Component: $COMPONENT${NC}"
echo -e "${BLUE}Project Root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}Image Tag: $TAG${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Build specific component
case $COMPONENT in
    "backend")
        echo -e "${YELLOW}📦 Building doc-proc-backend...${NC}"
        docker build -t "doc-proc-backend:$TAG" -f "Dockerfile.backend" "."
        ;;
    "worker")
        echo -e "${YELLOW}📦 Building doc-proc-worker...${NC}"
        docker build -t "doc-proc-worker:$TAG" -f "Dockerfile.worker" "."
        ;;
    "frontend")
        echo -e "${YELLOW}📦 Building doc-proc-frontend...${NC}"
        docker build -t "doc-proc-frontend:$TAG" -f "Dockerfile.frontend" "."
        ;;
    *)
        echo -e "${RED}❌ Unknown component: $COMPONENT${NC}"
        usage
        ;;
esac

echo -e "${GREEN}✅ Successfully built doc-proc-$COMPONENT:$TAG${NC}"
echo ""
echo -e "${BLUE}Image info:${NC}"
docker images | grep "doc-proc-$COMPONENT" | grep "$TAG"