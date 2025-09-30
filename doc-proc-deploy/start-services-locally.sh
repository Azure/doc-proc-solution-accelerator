#!/bin/bash

# Doc Processing Solution - Local Development Startup Script
# This script starts selected services locally for document pipeline execution

set -e

# Default service configuration
START_API=false
START_WORKER=false
START_WEB=false
START_ALL=true # By default, start all services if no options are provided

# Function to show usage
show_usage() {
    cat << EOF
🚀 Doc Processing Solution - Local Development Startup Script

Usage: $0 [OPTIONS]

OPTIONS:
    -a, --api       Start the backend API service only
    -w, --worker    Start the worker service only
    -e, --web       Start the web frontend only
    -h, --help      Show this help message

EXAMPLES:
    $0                          # Start all services (API, worker, web)
    $0 -a -w                    # Start API and worker only
    $0 --web                    # Start web frontend only
    $0 -a -e                    # Start API and web frontend

NOTES:
    - Services will run in the background with graceful shutdown on Ctrl+C
    - Web frontend will be available at http://localhost:8080 (or port shown by Vite)
    - Backend API will be available at http://localhost:8090
    - Worker runs in background for processing tasks

EOF
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--api)
            START_API=true
            START_ALL=false
            shift
            ;;
        -w|--worker)
            START_WORKER=true
            START_ALL=false
            shift
            ;;
        -e|--web)
            START_WEB=true
            START_ALL=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

echo "🚀 Starting selected Doc Processing Solution services..."
echo "Services to start:"
[ "$START_ALL" = true ] || [ "$START_API" = true ] && echo "  ✓ Backend API"
[ "$START_ALL" = true ] || [ "$START_WORKER" = true ] && echo "  ✓ Worker"
[ "$START_ALL" = true ] || [ "$START_WEB" = true ] && echo "  ✓ Web Frontend"

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check required dependencies
if [ "$START_ALL" = true ] || [ "$START_API" = true ] || [ "$START_WORKER" = true ]; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python is not available. Please install Python first."
        exit 1
    fi
fi

if [ "$START_ALL" = true ] || [ "$START_WEB" = true ]; then
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not available. Please install Node.js first."
        exit 1
    fi
    if ! command -v npm &> /dev/null; then
        echo "❌ npm is not available. Please install npm first."
        exit 1
    fi
fi

echo "🔧 Setting up environment..."

# Setup Python environment if Python services are selected
if [ "$START_ALL" = true ] ||[ "$START_API" = true ] || [ "$START_WORKER" = true ]; then
    # Check if virtual environment exists, create if not
    if [ ! -d "venv" ]; then
        echo "🐍 Creating virtual environment..."
        python -m venv venv
    fi

    # Activate virtual environment
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate

    # Install dependencies for each component
    echo "📦 Installing Python dependencies..."

    # Install doc-proc-lib
    if [ -d "doc-proc-lib" ]; then
        echo "  Installing doc-proc-lib..."
        cd doc-proc-lib
        pip install -e . > /dev/null 2>&1
        cd ..
    fi

    # Install api dependencies
    if ([ "$START_ALL" = true ] || [ "$START_API" = true ]) && [ -d "doc-proc-api" ]; then
        echo "  Installing API dependencies..."
        cd doc-proc-api
        pip install -r requirements.txt > /dev/null 2>&1
        cd ..
    fi

    # Install worker dependencies
    if ([ "$START_ALL" = true ] || [ "$START_WORKER" = true ]) && [ -d "doc-proc-worker" ]; then
        echo "  Installing Worker dependencies..."
        cd doc-proc-worker
        pip install -r requirements.txt > /dev/null 2>&1
        cd ..
    fi
fi

# Setup Node.js environment if web service is selected
if ([ "$START_ALL" = true ] || [ "$START_WEB" = true ]) && [ -d "doc-proc-web" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd doc-proc-web
    echo "  Installing web frontend dependencies..."
    npm install > /dev/null 2>&1
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
    graceful_stop "$API_PID" "Backend API"
    graceful_stop "$WORKER_PID" "Worker"
    graceful_stop "$WEB_PID" "Web Frontend"
    
    echo "✅ All services stopped gracefully"
    exit 0
}

trap cleanup EXIT INT TERM

echo "🎯 Starting services..."

# Initialize service tracking variables
WORKER_STARTED=false
API_STARTED=false
WEB_STARTED=false

# Start worker in background
if [ "$START_ALL" = true ] || [ "$START_WORKER" = true ]; then
    if [ -d "doc-proc-worker" ]; then
        echo "👷 Starting Worker..."
        cd doc-proc-worker
        python run_worker.py &
        WORKER_PID=$!
        cd ..
        
        # Check if worker process is still running after a short delay
        sleep 5
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
fi

# Wait a moment for worker to stabilize
if [ "$WORKER_STARTED" = true ]; then
    sleep 3
fi

# Start API in background
if [ "$START_ALL" = true ] || [ "$START_API" = true ]; then
    if [ -d "doc-proc-api" ]; then
        echo "🌐 Starting API..."
        cd doc-proc-api
        python main.py &
        API_PID=$!
        cd ..

        # Check if API process is still running after a short delay
        sleep 5
        if kill -0 $API_PID 2>/dev/null; then
            echo "✅ API started successfully (PID: $API_PID)"
            API_STARTED=true
        else
            echo "❌ API failed to start"
            API_PID=""
        fi
    else
        echo "⚠️ API directory not found, skipping API startup"
    fi
fi

# Start Web frontend in background
if [ "$START_ALL" = true ] || [ "$START_WEB" = true ]; then
    if [ -d "doc-proc-web" ]; then
        echo "🌐 Starting Web Frontend..."
        cd doc-proc-web
        npm run dev &
        WEB_PID=$!
        cd ..
        
        # Check if web process is still running after a short delay
        sleep 5
        if kill -0 $WEB_PID 2>/dev/null; then
            echo "✅ Web Frontend started successfully (PID: $WEB_PID)"
            WEB_STARTED=true
        else
            echo "❌ Web Frontend failed to start"
            WEB_PID=""
        fi
    else
        echo "⚠️ Web directory not found, skipping web startup"
    fi
fi

# Wait for services to be ready
if [ "$API_STARTED" = true ]; then
    echo "⏳ Waiting for API to be ready..."
    sleep 3
fi

if [ "$WEB_STARTED" = true ]; then
    echo "⏳ Waiting for Web Frontend to be ready..."
    sleep 3
fi

echo ""

# Count successfully started services
SERVICES_STARTED=0
SERVICES_SELECTED=0

[ "$START_WORKER" = true ] && SERVICES_SELECTED=$((SERVICES_SELECTED + 1))
[ "$START_API" = true ] && SERVICES_SELECTED=$((SERVICES_SELECTED + 1))
[ "$START_WEB" = true ] && SERVICES_SELECTED=$((SERVICES_SELECTED + 1))

[ "$WORKER_STARTED" = true ] && SERVICES_STARTED=$((SERVICES_STARTED + 1))
[ "$API_STARTED" = true ] && SERVICES_STARTED=$((SERVICES_STARTED + 1))
[ "$WEB_STARTED" = true ] && SERVICES_STARTED=$((SERVICES_STARTED + 1))

# Show startup results
if [ "$SERVICES_STARTED" -eq "$SERVICES_SELECTED" ] && [ "$SERVICES_STARTED" -gt 0 ]; then
    echo "🎉 All selected services started successfully!"
elif [ "$SERVICES_STARTED" -gt 0 ]; then
    echo "⚠️ Some services started with issues:"
    if [ "$START_WORKER" = true ]; then
        [ "$WORKER_STARTED" = true ] && echo "  ✅ Worker: Running" || echo "  ❌ Worker: Failed to start"
    fi
    if [ "$START_API" = true ]; then
        [ "$API_STARTED" = true ] && echo "  ✅ API: Running" || echo "  ❌ API: Failed to start"
    fi
    if [ "$START_WEB" = true ]; then
        [ "$WEB_STARTED" = true ] && echo "  ✅ Web Frontend: Running" || echo "  ❌ Web Frontend: Failed to start"
    fi
else
    echo "❌ Failed to start any services!"
    echo "Please check the error messages above and try again."
    exit 1
fi

echo ""
echo "📊 Service URLs:"
if [ "$API_STARTED" = true ]; then
    echo "  Backend API:    http://localhost:8090"
    echo "  API Docs:       http://localhost:8090/docs"
    echo "  Health Check:   http://localhost:8090/api/health"
fi
if [ "$WEB_STARTED" = true ]; then
    echo "  Web Frontend:   http://localhost:8080 (or port shown by Vite)"
fi
if [ "$WORKER_STARTED" = true ]; then
    echo "  Worker:         Running in background"
fi

echo ""
echo "🛠️ Development Tips:"
if [ "$API_STARTED" = true ]; then
    echo "  - API runs with --reload for auto-restart on changes"
fi
if [ "$WORKER_STARTED" = true ]; then
    echo "  - Worker runs in background for processing tasks"
fi
if [ "$WEB_STARTED" = true ]; then
    echo "  - Web frontend runs with hot reload for development"
fi
echo "  - Check logs above for any startup errors"
echo "  - Ctrl+C to stop all services gracefully"


# Build list of PIDs to wait for
PIDS_TO_WAIT=""
[ -n "$WORKER_PID" ] && PIDS_TO_WAIT="$PIDS_TO_WAIT $WORKER_PID"
[ -n "$API_PID" ] && PIDS_TO_WAIT="$PIDS_TO_WAIT $API_PID"
[ -n "$WEB_PID" ] && PIDS_TO_WAIT="$PIDS_TO_WAIT $WEB_PID"

# Wait for processes (only if they're running)
if [ -n "$PIDS_TO_WAIT" ]; then
    wait $PIDS_TO_WAIT
else
    echo "No services running to wait for."
    exit 1
fi
