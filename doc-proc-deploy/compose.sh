#!/bin/bash

# Doc Processing Solution - Docker Compose Management Script
# This script provides easy management of the entire solution using Docker Compose

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

# Default values
export TAG=${TAG:-"latest"}
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Change to script directory for docker-compose context
cd "$SCRIPT_DIR"

# Usage function
usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  up       - Start all services (build if needed)"
    echo "  down     - Stop and remove all services"
    echo "  build    - Build all images"
    echo "  start    - Start existing services"
    echo "  stop     - Stop services without removing"
    echo "  restart  - Restart all services"
    echo "  status   - Show service status"
    echo "  logs     - Show logs for all services or specific service"
    echo "  shell    - Open shell in a service container"
    echo ""
    echo "Service-specific commands:"
    echo "  up-backend   - Start backend and dependencies"
    echo "  up-worker    - Start worker and dependencies"  
    echo "  up-frontend  - Start frontend and dependencies"
    echo ""
    echo "Environment Variables:"
    echo "  TAG      - Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 up"
    echo "  $0 logs backend"
    echo "  $0 shell worker"
    echo "  TAG=dev $0 build"
    exit 1
}

# Main script logic
case "${1:-}" in
    "up")
        echo -e "${BLUE}🚀 Starting Doc Processing Solution with Docker Compose...${NC}"
        docker-compose -f "$COMPOSE_FILE" up -d
        echo ""
        echo -e "${GREEN}✅ All services started!${NC}"
        echo -e "${BLUE}🌐 Access URLs:${NC}"
        echo -e "${GREEN}Frontend: http://localhost:8080${NC}"
        echo -e "${GREEN}Backend API: http://localhost:8090${NC}"
        ;;
    "down")
        echo -e "${YELLOW}🛑 Stopping and removing all services...${NC}"
        docker-compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}✅ All services stopped and removed${NC}"
        ;;
    "build")
        echo -e "${BLUE}🔨 Building all images...${NC}"
        docker-compose -f "$COMPOSE_FILE" build --parallel
        echo -e "${GREEN}✅ All images built successfully${NC}"
        ;;
    "start")
        echo -e "${BLUE}▶️  Starting existing services...${NC}"
        docker-compose -f "$COMPOSE_FILE" start
        echo -e "${GREEN}✅ Services started${NC}"
        ;;
    "stop")
        echo -e "${YELLOW}⏸️  Stopping services...${NC}"
        docker-compose -f "$COMPOSE_FILE" stop
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
    "restart")
        echo -e "${BLUE}🔄 Restarting all services...${NC}"
        docker-compose -f "$COMPOSE_FILE" restart
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
    "status")
        echo -e "${BLUE}📊 Service Status:${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        if [ -n "$2" ]; then
            echo -e "${BLUE}📋 Showing logs for $2...${NC}"
            docker-compose -f "$COMPOSE_FILE" logs -f "$2"
        else
            echo -e "${BLUE}📋 Showing logs for all services...${NC}"
            docker-compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;
    "shell")
        if [ -n "$2" ]; then
            echo -e "${BLUE}🐚 Opening shell in $2...${NC}"
            docker-compose -f "$COMPOSE_FILE" exec "$2" /bin/bash
        else
            echo -e "${RED}❌ Please specify a service name${NC}"
            exit 1
        fi
        ;;
    "up-backend")
        echo -e "${BLUE}🚀 Starting backend...${NC}"
        docker-compose -f "$COMPOSE_FILE" up -d backend
        ;;
    "up-worker")
        echo -e "${BLUE}👷 Starting worker...${NC}"
        docker-compose -f "$COMPOSE_FILE" up -d worker
        ;;
    "up-frontend")
        echo -e "${BLUE}🎨 Starting frontend and dependencies...${NC}"
        docker-compose -f "$COMPOSE_FILE" up -d backend frontend
        ;;
    *)
        usage
        ;;
esac