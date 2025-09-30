# Document Processing Worker

High-performance document processing worker service that provides scalable, fault-tolerant execution of document processing pipelines. The worker polls Azure Storage Queues for batch execution requests and processes them using either single-worker or multiprocessing architectures.

## Overview

The doc-proc-worker is a critical component of the document processing solution accelerator, designed to handle large-scale document processing workloads with enterprise-grade reliability and performance. It integrates with Azure Cosmos DB for state management and Azure Storage Queues for distributed task coordination.

### Key Capabilities

- **Asynchronous Queue Processing**: High-throughput polling and processing of Azure Storage Queue messages
- **Pipeline Execution**: Executes configurable document processing pipelines with step-by-step orchestration  
- **Batch Processing**: Handles batch operations with progress tracking, error recovery, and results aggregation
- **Multiprocessing Support**: Scales to multiple concurrent worker processes for CPU-intensive workloads
- **Fault Tolerance**: Comprehensive error handling, retry mechanisms, and graceful degradation
- **Health Monitoring**: Real-time worker health checks with automatic restart capabilities
- **Graceful Shutdown**: Coordinated shutdown handling across all worker processes
- **Cloud-Native**: Built for Azure with native integration to Azure services

### Architecture Components

- **Queue Worker**: Core async worker that processes individual queue messages
- **Execution Manager**: Orchestrates pipeline execution and batch processing  
- **Pipeline Manager**: Loads and manages document processing pipelines
- **Worker Pool Manager**: Manages multiprocessing pools with health monitoring
- **Azure Service Proxies**: Abstractions for Azure Cosmos DB and Storage Queue interactions

## Processing Flow

### Message Processing Lifecycle

1. **Queue Polling**: Workers continuously poll Azure Storage Queue for new messages
2. **Message Deserialization**: JSON messages are parsed into typed request objects  
3. **Message Validation**: Request validation and type checking
4. **Batch Execution**:
   - Create BatchExecution record in Cosmos DB
   - Load pipeline configuration and steps
   - Process documents through pipeline stages
   - Track progress and collect results
   - Update batch status and completion metrics
5. **Result Storage**: Store execution results and statistics in Cosmos DB
6. **Queue Cleanup**: Delete successfully processed messages from queue

### Supported Message Types

- **BATCH_EXECUTION_REQUEST**: Primary message type for initiating document processing batches
- **BATCH_RETRY_REQUEST**: Retry failed batch executions with exponential backoff
- **BATCH_CANCEL_REQUEST**: Cancel running batch executions

### Pipeline Execution

The worker integrates with the doc-proc-lib pipeline framework:

- Loads pipeline configurations dynamically  
- Executes step-by-step document processing
- Handles step dependencies and data flow
- Provides error isolation and recovery
- Aggregates step outputs into batch results

## Architecture

### Processing Models

#### Single Worker Mode
- **Use Case**: Development, testing, low-throughput scenarios
- **Architecture**: Single async event loop with sequential message processing
- **Benefits**: Simple deployment, predictable resource usage, easier debugging
- **Limitations**: Cannot fully utilize multi-core systems, limited throughput

#### Multiprocessing Pool Mode  
- **Use Case**: Production workloads, high-throughput scenarios, CPU-intensive processing
- **Architecture**: Multiple worker processes, each with independent async event loops
- **Benefits**: 
  - Full CPU utilization across cores
  - Process isolation prevents cascading failures  
  - Horizontal scaling within single instance
  - Fault tolerance through worker restart
- **Coordination**: Shared shutdown events and health monitoring across processes

### Core Data Models

#### BatchExecution
Tracks the lifecycle of document processing batches:
- **Status Management**: SUBMITTED → RUNNING → COMPLETED/FAILED/CANCELLED
- **Progress Tracking**: Document counts, completion rates, timing metrics
- **Metadata Storage**: Pipeline configuration, source information, custom attributes

#### QueueMessage Types
- **QueueBatchExecutionRequest**: Pipeline name, document list, priority, retry configuration
- **QueueMessageWrapper**: Message envelope with processing metadata and error tracking

#### Worker Statistics
- **Performance Metrics**: Processing times, success rates, throughput statistics
- **Health Indicators**: Worker status, current activity, resource utilization
- **Operational Data**: Message counts, error rates, retry statistics

## Quick Start

### Single Worker (Development/Testing)
```bash
# Basic single worker
python run_queue_worker.py

# With debug logging
LOG_LEVEL=DEBUG python run_queue_worker.py
```

### Multiprocessing Pool (Production)
```bash
# Default configuration (CPU count workers)
python run_queue_worker.py --pool

# Custom worker count
python run_queue_worker.py --pool --workers 4

# Disable auto-restart for troubleshooting
python run_queue_worker.py --pool --no-restart

# Alternative dedicated script
python run_worker_pool.py
```

### Docker Quick Start
```bash
# Single worker
docker run -e COSMOS_DB_ENDPOINT="<endpoint>" \
           -e STORAGE_ACCOUNT_WORKER_QUEUE_URL="<queue-url>" \
           doc-proc-worker:latest

# Multiprocessing pool
docker run -e WORKER_POOL_SIZE=4 \
           -e WORKER_AUTO_RESTART=true \
           doc-proc-worker:latest python run_queue_worker.py --pool
```

## Configuration

### Environment Variables

#### Azure Services
```bash
# Azure Cosmos DB - Document storage and state management
COSMOS_DB_ENDPOINT="https://<your-account>.documents.azure.com:443/"
COSMOS_DB_NAME="docproc"                                      # Database name

# Container names for different data types
COSMOS_DB_CONTAINER_PIPELINES="pipelines"                    # Pipeline configurations
COSMOS_DB_CONTAINER_STEP_CATALOG="step_catalog"              # Available processing steps
COSMOS_DB_CONTAINER_STEP_INSTANCES="step_instances"          # Step configurations
COSMOS_DB_CONTAINER_SERVICE_CATALOG="service_catalog"        # Available services
COSMOS_DB_CONTAINER_SERVICE_INSTANCES="service_instances"    # Service configurations
COSMOS_DB_CONTAINER_BATCH_EXECUTIONS="batch_executions"      # Batch execution tracking
COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS="pipeline_executions" # Pipeline execution results

# Azure Storage Queue - Message coordination  
STORAGE_ACCOUNT_WORKER_QUEUE_URL="https://<account>.queue.core.windows.net/"
STORAGE_WORKER_QUEUE_NAME="docproc-execution-requests"       # Queue name for execution requests
```

#### Worker Configuration  
```bash
# Logging and debugging
LOG_LEVEL="INFO"                    # Logging level: DEBUG, INFO, WARNING, ERROR
DEBUG=false                         # Enable debug mode

# API server settings (if running HTTP API)
API_SERVER_HOST="0.0.0.0"          # API server bind address  
API_SERVER_PORT=8010                # API server port
API_SERVER_WORKERS=4                # Number of API workers
```

#### Multiprocessing Pool Configuration
```bash
# Worker pool sizing
WORKER_POOL_SIZE=0                           # Number of worker processes (0 = auto-detect CPU count)

# Health and reliability
WORKER_AUTO_RESTART=true                     # Automatically restart failed workers
WORKER_SHUTDOWN_TIMEOUT=30                   # Maximum time to wait for graceful shutdown (seconds)
WORKER_HEALTH_CHECK_INTERVAL=10              # Interval for checking worker health (seconds)
```

#### Performance Tuning
```bash
# Message processing configuration
POLL_INTERVAL_SECONDS=5                      # How often to check for new messages
MAX_MESSAGES_PER_POLL=5                      # Maximum messages to process per poll
MESSAGE_VISIBILITY_TIMEOUT=300               # Message visibility timeout (5 minutes)  
MAX_PROCESSING_TIME=600                      # Maximum processing time per message (10 minutes)
```

### Configuration File Support

The worker also supports configuration via `.env` files placed in the project root:

```bash
# .env file example
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_NAME=docproc
STORAGE_ACCOUNT_WORKER_QUEUE_URL=https://yourstorage.queue.core.windows.net/
STORAGE_WORKER_QUEUE_NAME=docproc-execution-requests
LOG_LEVEL=INFO
WORKER_POOL_SIZE=4
WORKER_AUTO_RESTART=true
```

## Development Setup

### Prerequisites

#### Required Services
- **Python 3.8+**: Runtime environment
- **Azure Cosmos DB**: Document database for state management
- **Azure Storage Account**: Queue service for message coordination  
- **Azure Active Directory**: Authentication and authorization (or use connection strings)

#### Optional Services
- **Redis**: For caching and session management (if using Celery features)
- **Application Insights**: For advanced monitoring and telemetry

### Local Development Environment

#### 1. Environment Setup
```bash
# Clone repository and navigate to worker directory
git clone <repo-url>
cd doc-proc-solution-accelerator/doc-proc-worker

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Azure service endpoints and credentials
# At minimum, configure:
# - COSMOS_DB_ENDPOINT
# - STORAGE_ACCOUNT_WORKER_QUEUE_URL
# - Authentication method (Azure credentials or connection strings)
```

#### 3. Azure Service Setup
```bash
# Create required Cosmos DB containers (if not exists)
# The worker will attempt to create containers automatically
# Or run setup script:
python -c "from app.setup import setup_cosmos_containers; setup_cosmos_containers()"
```

#### 4. Running the Worker
```bash
# Development: Single worker with debug logging
LOG_LEVEL=DEBUG python run_queue_worker.py

# Production-like: Multiprocessing pool  
python run_queue_worker.py --pool --workers 2

# Test with sample messages
python quick_queue_test.py
```

### Testing and Validation

#### Unit Tests
```bash
# Run comprehensive test suite
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_queue_worker.py -v
python -m pytest tests/test_worker_pool.py -v
python -m pytest tests/test_execution_manager.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

#### Integration Tests  
```bash
# Test queue integration
python quick_queue_test.py

# Test multiprocessing functionality
python tests/test_multiprocessing.py

# Test with sample pipeline
python demo/test_pipeline_execution.py
```

#### Performance Testing
```bash
# Load testing with multiple messages
python tests/performance/test_throughput.py --messages 100 --workers 4

# Memory usage monitoring
python tests/performance/test_memory_usage.py --duration 300
```

## Deployment

### Docker Containerization

#### Build Image
```bash
# Build production image
docker build -t doc-proc-worker:latest .

# Build with specific Python version
docker build -t doc-proc-worker:python3.11 --build-arg PYTHON_VERSION=3.11 .
```

#### Single Worker Deployment
```bash
docker run -d \
  --name doc-proc-worker \
  -e COSMOS_DB_ENDPOINT="${COSMOS_DB_ENDPOINT}" \
  -e STORAGE_ACCOUNT_WORKER_QUEUE_URL="${STORAGE_ACCOUNT_WORKER_QUEUE_URL}" \
  -e LOG_LEVEL="INFO" \
  --restart unless-stopped \
  doc-proc-worker:latest
```

#### Multiprocessing Pool Deployment  
```bash
docker run -d \
  --name doc-proc-worker-pool \
  -e WORKER_POOL_SIZE=4 \
  -e WORKER_AUTO_RESTART=true \
  -e WORKER_SHUTDOWN_TIMEOUT=30 \
  -e COSMOS_DB_ENDPOINT="${COSMOS_DB_ENDPOINT}" \
  -e STORAGE_ACCOUNT_WORKER_QUEUE_URL="${STORAGE_ACCOUNT_WORKER_QUEUE_URL}" \
  --restart unless-stopped \
  doc-proc-worker:latest python run_queue_worker.py --pool
```

### Container Orchestration

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  doc-proc-worker:
    build: 
      context: .
      dockerfile: Dockerfile
    command: python run_queue_worker.py --pool
    environment:
      # Azure Services
      - COSMOS_DB_ENDPOINT=${COSMOS_DB_ENDPOINT}
      - COSMOS_DB_NAME=${COSMOS_DB_NAME:-docproc}
      - STORAGE_ACCOUNT_WORKER_QUEUE_URL=${STORAGE_ACCOUNT_WORKER_QUEUE_URL}
      - STORAGE_WORKER_QUEUE_NAME=${STORAGE_WORKER_QUEUE_NAME:-docproc-execution-requests}
      
      # Worker Configuration  
      - WORKER_POOL_SIZE=${WORKER_POOL_SIZE:-4}
      - WORKER_AUTO_RESTART=${WORKER_AUTO_RESTART:-true}
      - WORKER_SHUTDOWN_TIMEOUT=${WORKER_SHUTDOWN_TIMEOUT:-30}
      
      # Logging
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      
    volumes:
      # Mount configuration files if needed
      - ./config:/app/config:ro
      
    restart: unless-stopped
    
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 1G
          cpus: '1'
    
    # Health check
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8010/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Redis for advanced features
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis-data:/data
    
volumes:
  redis-data:
```

#### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doc-proc-worker
  labels:
    app: doc-proc-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: doc-proc-worker
  template:
    metadata:
      labels:
        app: doc-proc-worker
    spec:
      containers:
      - name: doc-proc-worker
        image: doc-proc-worker:latest
        command: ["python", "run_queue_worker.py", "--pool"]
        env:
        - name: COSMOS_DB_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: cosmos-db-endpoint
        - name: STORAGE_ACCOUNT_WORKER_QUEUE_URL
          valueFrom:
            secretKeyRef:
              name: azure-secrets  
              key: storage-queue-url
        - name: WORKER_POOL_SIZE
          value: "2"
        - name: LOG_LEVEL
          value: "INFO"
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi" 
            cpu: "500m"
            
        livenessProbe:
          exec:
            command: ["python", "-c", "import os; exit(0 if os.path.exists('/tmp/worker-healthy') else 1)"]
          initialDelaySeconds: 30
          periodSeconds: 30
          
        readinessProbe:
          exec:
            command: ["python", "-c", "import os; exit(0 if os.path.exists('/tmp/worker-ready') else 1)"]
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Secret
metadata:
  name: azure-secrets
type: Opaque
stringData:
### Azure Container Apps Deployment

#### Bicep Infrastructure Template
```bash
# Set deployment parameters
RESOURCE_GROUP="docproc-rg"
LOCATION="westeurope"  
APP_IMAGE="youracr.azurecr.io/doc-proc-worker:latest"

# Create resource group
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# Deploy infrastructure and application
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/bicep/main.bicep \
  --parameters \
    location="$LOCATION" \
    containerImage="$APP_IMAGE" \
    namePrefix="docproc" \
    cosmosDbName="docproc" \
    workerPoolSize=4 \
    minReplicas=1 \
    maxReplicas=10

# Get the deployed worker service status
az containerapp show \
  --name docproc-worker \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.provisioningState"
```

#### Manual Azure Container Apps Setup
```bash
# Create Container Apps Environment
az containerapp env create \
  --name docproc-env \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

# Deploy worker with multiprocessing
az containerapp create \
  --name doc-proc-worker \
  --resource-group "$RESOURCE_GROUP" \
  --environment docproc-env \
  --image "$APP_IMAGE" \
  --command "python" "run_queue_worker.py" "--pool" \
  --env-vars \
    COSMOS_DB_ENDPOINT="${COSMOS_DB_ENDPOINT}" \
    STORAGE_ACCOUNT_WORKER_QUEUE_URL="${STORAGE_ACCOUNT_WORKER_QUEUE_URL}" \
    WORKER_POOL_SIZE=4 \
    WORKER_AUTO_RESTART=true \
    LOG_LEVEL=INFO \
  --cpu 2.0 \
  --memory 4.0Gi \
  --min-replicas 1 \
  --max-replicas 5 \
  --scale-rule-name queue-length \
  --scale-rule-type azure-queue \
  --scale-rule-metadata queueName=docproc-execution-requests queueLength=10 \
  --scale-rule-auth connection=queue-connection-string
```

## Monitoring and Observability

### Health Checks and Probes

#### Built-in Health Endpoints  
```bash
# Worker health status (if API enabled)
curl http://localhost:8010/health

# Detailed worker statistics
curl http://localhost:8010/metrics

# Readiness check
curl http://localhost:8010/ready
```

#### Custom Health Check Script
```python
# health_check.py
import asyncio
import sys
from app.queue_worker import QueueWorker
from app.dependencies import get_queue_proxy

async def check_worker_health():
    """Health check script for worker"""
    try:
        # Test queue connectivity
        queue_proxy = get_queue_proxy()
        await queue_proxy.connect()
        
        # Test worker initialization
        worker = QueueWorker("health-check")
        await worker._initialize_services()
        
        print("✅ Worker health check passed")
        return True
        
    except Exception as e:
        print(f"❌ Worker health check failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_worker_health())
    sys.exit(0 if result else 1)
```

### Logging and Metrics

#### Structured Logging Configuration
```python
# Custom logging configuration
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(worker_id)s] - %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "worker_id": "%(worker_id)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/worker.log',
            'formatter': 'json',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'doc-proc-worker': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

#### Performance Metrics Collection
```bash
# Enable metrics collection
pip install prometheus-client

# Add metrics endpoint to worker
# Metrics available at http://localhost:8010/metrics
```

### Azure Application Insights Integration

#### Configuration
```bash
# Environment variables for Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/"
APPINSIGHTS_INSTRUMENTATIONKEY="your-instrumentation-key"
```

#### Custom Telemetry
```python
# Telemetry integration example
from applicationinsights import TelemetryClient
from applicationinsights.logging import LoggingHandler

# Initialize telemetry client
tc = TelemetryClient('your-instrumentation-key')

# Track custom events
tc.track_event('BatchProcessingStarted', {
    'batch_id': batch.id,
    'pipeline_name': batch.pipeline_name,
    'document_count': len(batch.documents)
})

# Track performance metrics
tc.track_metric('ProcessingTime', processing_time_ms)
tc.track_metric('QueueDepth', queue_depth)
```

## Troubleshooting

### Common Issues

#### Worker Startup Problems
```bash
# Check environment variables
python -c "from app.settings import app_settings; print(vars(app_settings))"

# Verify Azure connectivity
python -c "from app.dependencies import get_queue_proxy; import asyncio; asyncio.run(get_queue_proxy().connect())"

# Test Cosmos DB connection
python -c "from app.dependencies import get_cosmos_db; db = get_cosmos_db(); print('Connected' if db else 'Failed')"
```

#### Performance Issues
```bash
# Monitor queue depth
python -c "from app.proxy.queue import StorageQueue; import asyncio; print(asyncio.run(StorageQueue().get_queue_depth()))"

# Check worker resource usage
docker stats doc-proc-worker

# Monitor multiprocessing pool
LOG_LEVEL=DEBUG python run_queue_worker.py --pool
```

#### Memory Issues
```bash  
# Monitor memory usage per worker
python -c "
import psutil
for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
    if 'run_queue_worker' in proc.info['name']:
        print(f'PID: {proc.info[\"pid\"]}, Memory: {proc.info[\"memory_info\"].rss / 1024 / 1024:.1f}MB')
"

# Check for memory leaks
python -m memory_profiler run_queue_worker.py
```

### Debug Mode Operations

#### Verbose Logging
```bash
# Maximum verbosity
LOG_LEVEL=DEBUG python run_queue_worker.py

# Trace-level logging with stack traces  
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from run_queue_worker import main
main()
"
```

#### Interactive Debugging
```python
# Debug mode with breakpoints
import pdb; pdb.set_trace()

# Remote debugging (if needed)
import debugpy
debugpy.listen(('0.0.0.0', 5678))
debugpy.wait_for_client()
```

## Security Considerations

### Authentication and Authorization

#### Azure Active Directory Integration
```bash
# Use Azure AD authentication (recommended)
az login
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"  
export AZURE_TENANT_ID="your-tenant-id"
```

#### Managed Identity (Production)
```bash
# Enable managed identity for Container Apps/AKS
# No secrets needed in environment variables
export AZURE_USE_MANAGED_IDENTITY=true
```

#### Connection String Security (Development)
```bash
# Use Azure Key Vault for secrets management
export COSMOS_DB_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://vault.vault.azure.net/secrets/cosmos-connection/)"
export STORAGE_ACCOUNT_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://vault.vault.azure.net/secrets/storage-connection/)"
```

### Network Security

#### Private Endpoints
- Configure private endpoints for Cosmos DB and Storage Account
- Use VNet integration for Container Apps
- Implement network security groups for traffic filtering

#### Data Encryption
- Enable encryption at rest for Cosmos DB and Storage
- Use TLS 1.2+ for all communications
- Implement Azure Key Vault for secret management

## Performance Optimization

### Sizing Guidelines

#### Worker Pool Sizing
- **CPU-intensive workloads**: Start with CPU core count
- **I/O-intensive workloads**: Use 2x CPU core count  
- **Memory-constrained**: Reduce workers to manage memory usage
- **Queue throughput**: Match worker capacity to message arrival rate

#### Resource Allocation
```yaml
# Container resource recommendations
resources:
  requests:
    memory: "1Gi"      # Base memory per worker
    cpu: "500m"        # Base CPU per worker
  limits:
    memory: "4Gi"      # Maximum memory (pool + overhead)
    cpu: "2000m"       # Maximum CPU usage
```

#### Scaling Configuration
```bash
# Auto-scaling based on queue depth
SCALE_MIN_REPLICAS=1           # Minimum container instances
SCALE_MAX_REPLICAS=10          # Maximum container instances  
SCALE_QUEUE_THRESHOLD=20       # Messages per replica
SCALE_CPU_THRESHOLD=70         # CPU percentage threshold
SCALE_MEMORY_THRESHOLD=80      # Memory percentage threshold
```

### Performance Tuning

#### Message Processing Optimization
```bash
# Batch processing tuning
MAX_MESSAGES_PER_POLL=10       # Increase for higher throughput
POLL_INTERVAL_SECONDS=2        # Reduce for lower latency
MESSAGE_VISIBILITY_TIMEOUT=600 # Increase for longer processing

# Pipeline optimization  
PIPELINE_CACHE_SIZE=100        # Cache loaded pipelines
STEP_PARALLEL_EXECUTION=true   # Enable parallel step execution
```

#### Database Performance
```bash
# Cosmos DB optimization
COSMOS_DB_MAX_CONNECTIONS=20   # Connection pooling
COSMOS_DB_REQUEST_TIMEOUT=30   # Request timeout seconds
COSMOS_DB_RETRY_MAX_ATTEMPTS=3 # Retry configuration
```

For detailed information about multiprocessing architecture and patterns, see [MULTIPROCESSING.md](MULTIPROCESSING.md).

## References

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure Cosmos DB Best Practices](https://docs.microsoft.com/en-us/azure/cosmos-db/best-practices)
- [Azure Storage Queue Documentation](https://docs.microsoft.com/en-us/azure/storage/queues/)
- [Python Multiprocessing Guide](https://docs.python.org/3/library/multiprocessing.html)
- [Doc-Proc-Lib Pipeline Framework](../doc-proc-lib/README.md)
