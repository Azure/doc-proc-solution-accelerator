#!/bin/bash

# Doc Processing Solution - Local Development Startup Script
# This script starts all required services locally for document pipeline execution

set -e

echo "🚀 Starting Doc Processing Solution (Local Development)..."

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not available. Please install Python first."
    exit 1
fi

echo "🔧 Setting up environment..."

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "� Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies for each component
echo "📦 Installing dependencies..."

# Install doc-proc-lib
if [ -d "doc-proc-lib" ]; then
    echo "  Installing doc-proc-lib..."
    cd doc-proc-lib
    pip install -e . > /dev/null 2>&1
    cd ..
fi

# Install backend dependencies
if [ -d "doc-proc-ui/backend-app" ]; then
    echo "  Installing backend dependencies..."
    cd doc-proc-ui/backend-app
    pip install -r requirements.txt > /dev/null 2>&1
    cd ../..
fi

# Install worker dependencies
if [ -d "doc-proc-worker" ]; then
    echo "  Installing worker dependencies..."
    cd doc-proc-worker
    pip install -r requirements.txt > /dev/null 2>&1
    cd ..
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Gracefully shutting down services..."
    
    # Function to gracefully stop a process
    graceful_stop() {
        local pid=$1
        local name=$2
        local timeout=10
        
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "  Stopping $name (PID: $pid)..."
            
            # Send SIGTERM for graceful shutdown
            kill -TERM "$pid" 2>/dev/null || return 1
            
            # Wait for process to terminate gracefully
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt $timeout ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Check if process is still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "    $name didn't stop gracefully, forcing termination..."
                kill -KILL "$pid" 2>/dev/null || true
                sleep 1
            fi
            
            echo "  ✅ $name stopped"
        fi
    }
    
    # Stop services gracefully
    graceful_stop "$BACKEND_PID" "Backend API"
    graceful_stop "$WORKER_PID" "Worker"
    
    echo "✅ All services stopped gracefully"
    exit 0
}

trap cleanup EXIT INT TERM

echo "🎯 Starting services..."

# Start worker in background
WORKER_STARTED=false
if [ -d "doc-proc-worker" ]; then
    echo "👷 Starting Worker..."
    cd doc-proc-worker
    python run_worker.py &
    WORKER_PID=$!
    cd ..
    
    # Check if worker process is still running after a short delay
    sleep 10
    if kill -0 $WORKER_PID 2>/dev/null; then
        echo "✅ Worker started successfully (PID: $WORKER_PID)"
        WORKER_STARTED=true
    else
        echo "❌ Worker failed to start"
        WORKER_PID=""
    fi
else
    echo "⚠️ Worker directory not found, skipping worker startup"
fi

# Wait a moment for worker to stabilize
if [ "$WORKER_STARTED" = true ]; then
    sleep 5
fi

# Start backend API in background
BACKEND_STARTED=false
if [ -d "doc-proc-ui/backend-app" ]; then
    echo "🌐 Starting Backend API..."
    cd doc-proc-ui/backend-app
    python main.py &
    BACKEND_PID=$!
    cd ../..
    
    # Check if backend process is still running after a short delay
    sleep 10
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "✅ Backend API started successfully (PID: $BACKEND_PID)"
        BACKEND_STARTED=true
    else
        echo "❌ Backend API failed to start"
        BACKEND_PID=""
    fi
else
    echo "⚠️ Backend directory not found, skipping backend startup"
fi

# Wait for services to be ready
if [ "$BACKEND_STARTED" = true ]; then
    echo "⏳ Waiting for Backend API to be ready..."
    sleep 5
fi

echo ""

# Show startup results
if [ "$WORKER_STARTED" = true ] && [ "$BACKEND_STARTED" = true ]; then
    echo "🎉 All services started successfully!"
elif [ "$WORKER_STARTED" = true ] || [ "$BACKEND_STARTED" = true ]; then
    echo "⚠️ Some services started with issues:"
    [ "$WORKER_STARTED" = true ] && echo "  ✅ Worker: Running"
    [ "$WORKER_STARTED" = false ] && echo "  ❌ Worker: Failed to start"
    [ "$BACKEND_STARTED" = true ] && echo "  ✅ Backend API: Running"
    [ "$BACKEND_STARTED" = false ] && echo "  ❌ Backend API: Failed to start"
else
    echo "❌ Failed to start services!"
    echo "Please check the error messages above and try again."
    exit 1
fi

echo ""
echo "📊 Service URLs:"
if [ "$BACKEND_STARTED" = true ]; then
    echo "  Backend API:    http://localhost:8090"
    echo "  API Docs:       http://localhost:8090/docs"
    echo "  Health Check:   http://localhost:8090/health"
else
    echo "  Backend API:    ❌ Not running"
fi
echo ""
echo "Next Steps:"
echo "➡️ Frontend Development:"
echo "  To start the frontend, run:"
echo "  cd doc-proc-ui/web-app && npm install && npm run dev"
echo "  Then visit: http://localhost:8080 (or the port shown by Vite)"
echo ""
echo "🛠️ Development Tips:"
echo "  - Backend API runs with --reload for auto-restart on changes"
echo "  - Worker runs in background for processing tasks"
echo "  - Check logs above for any startup errors"
echo ""
echo "📝 Example API usage:"
echo '  curl -X GET http://localhost:8090/health'
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes (only if they're running)
if [ -n "$WORKER_PID" ] && [ -n "$BACKEND_PID" ]; then
    wait $WORKER_PID $BACKEND_PID
elif [ -n "$WORKER_PID" ]; then
    wait $WORKER_PID
elif [ -n "$BACKEND_PID" ]; then
    wait $BACKEND_PID
else
    echo "No services running to wait for."
    exit 1
fi
