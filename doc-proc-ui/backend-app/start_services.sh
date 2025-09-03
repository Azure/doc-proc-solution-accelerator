#!/bin/bash

# Doc Processing Solution - Startup Script
# This script starts all required services for document pipeline execution

set -e

echo "🚀 Starting Doc Processing Solution..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Redis for Celery
echo "📡 Starting Redis server..."
docker-compose up -d redis

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
until docker-compose exec redis redis-cli ping 2>/dev/null; do
    sleep 1
done
echo "✅ Redis is ready"

# Set default environment variables if not set
export CELERY_BROKER_URL=${CELERY_BROKER_URL:-"redis://localhost:6379/0"}
export CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND:-"redis://localhost:6379/0"}

echo "🔧 Environment variables:"
echo "  CELERY_BROKER_URL=$CELERY_BROKER_URL"
echo "  CELERY_RESULT_BACKEND=$CELERY_RESULT_BACKEND"

# Check if Python environment is set up
if ! python -c "import celery" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "🎯 Starting services..."

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    kill $CELERY_PID 2>/dev/null || true
    kill $API_PID 2>/dev/null || true
    docker-compose stop redis
    exit 0
}

trap cleanup EXIT INT TERM

# Start Celery worker in background
echo "👷 Starting Celery worker..."
celery -A app.celery_app worker --loglevel=info --concurrency=4 &
CELERY_PID=$!

# Wait a moment for Celery to start
sleep 3

# Start FastAPI server in background
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📊 Service URLs:"
echo "  API Server:     http://localhost:8000"
echo "  API Docs:       http://localhost:8000/docs"
echo "  Health Check:   http://localhost:8000/health"
echo ""
echo "🔧 Optional monitoring services:"
echo "  Flower (Celery): docker-compose --profile monitoring up flower -d"
echo "                   Then visit: http://localhost:5555"
echo "  Redis Commander: docker-compose --profile ui up redis-commander -d"
echo "                   Then visit: http://localhost:8081"
echo ""
echo "📝 Example API usage:"
echo '  curl -X POST http://localhost:8000/api/executions/ \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{'
echo '      "pipeline_instance_id": "your_pipeline_id",'
echo '      "documents": [{'
echo '        "container_name": "documents",'
echo '        "blob_name": "sample.pdf",'
echo '        "url": "https://your-storage.../sample.pdf"'
echo '      }]'
echo '    }'"'"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait $CELERY_PID $API_PID
