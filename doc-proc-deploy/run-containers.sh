#!/bin/bash

# Doc Processing Solution - Container Management Script
# This script manages Docker containers for the document processing solution

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
TAG=${TAG:-"latest"}
NETWORK_NAME="doc-proc-network"

# Create Docker network if it doesn't exist
create_network() {
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        echo -e "${BLUE}🌐 Creating Docker network: $NETWORK_NAME${NC}"
        docker network create "$NETWORK_NAME"
    fi
}

# Start backend service
start_backend() {
    echo -e "${YELLOW}🚀 Starting Backend API...${NC}"
    docker run -d \
        --name doc-proc-backend \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        -p 8090:8090 \
        doc-proc-backend:$TAG
    
    echo -e "${GREEN}✅ Backend API started on http://localhost:8090${NC}"
}

# Start worker service
start_worker() {
    echo -e "${YELLOW}👷 Starting Worker...${NC}"
    docker run -d \
        --name doc-proc-worker \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        doc-proc-worker:$TAG
    
    echo -e "${GREEN}✅ Worker started${NC}"
}

# Start frontend service
start_frontend() {
    echo -e "${YELLOW}🎨 Starting Frontend...${NC}"
    docker run -d \
        --name doc-proc-frontend \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        -p 8080:8080 \
        doc-proc-frontend:$TAG
    
    echo -e "${GREEN}✅ Frontend started on http://localhost:8080${NC}"
}

# Stop all services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    
    containers=("doc-proc-frontend" "doc-proc-backend" "doc-proc-worker")
    
    for container in "${containers[@]}"; do
        if docker ps -a --format "table {{.Names}}" | grep -q "^$container$"; then
            echo -e "${BLUE}Stopping $container...${NC}"
            docker stop "$container" &> /dev/null || true
            docker rm "$container" &> /dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Show service status
show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo ""
    
    containers=("doc-proc-backend" "doc-proc-worker" "doc-proc-frontend")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "$container"; then
            echo -e "${GREEN}✅ $container: Running${NC}"
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$container"
        else
            echo -e "${RED}❌ $container: Not running${NC}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo -e "${GREEN}Frontend: http://localhost:8080${NC}"
    echo -e "${GREEN}Backend API: http://localhost:8090${NC}"
}

# Show logs for a service
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        echo -e "${RED}Please specify a service: backend, worker, frontend${NC}"
        exit 1
    fi
    
    container_name="doc-proc-$service"
    
    if docker ps -a --format "table {{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${BLUE}📋 Showing logs for $service...${NC}"
        docker logs -f "$container_name"
    else
        echo -e "${RED}❌ Container $container_name not found${NC}"
    fi
}

# Usage function
usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start    - Start all services"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show service status"
    echo "  logs     - Show logs for a service (usage: logs <service>)"
    echo ""
    echo "Environment Variables:"
    echo "  TAG      - Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 status"
    echo "  $0 logs backend"
    echo "  TAG=dev $0 start"
    exit 1
}

# Main script logic
case "${1:-}" in
    "start")
        echo -e "${BLUE}🚀 Starting Doc Processing Solution...${NC}"
        create_network
        start_backend
        start_worker
        start_frontend
        echo ""
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        echo -e "${BLUE}🔄 Restarting services...${NC}"
        create_network
        start_backend
        start_worker
        start_frontend
        echo ""
        show_status
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    *)
        usage
        ;;
esac