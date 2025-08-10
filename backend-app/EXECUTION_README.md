# Pipeline Execution Service

This document describes the pipeline execution service that provides batch document processing capabilities using Celery for asynchronous task execution.

## Overview

The execution service allows you to:
- Submit batches of documents for pipeline processing
- Execute pipeline instances asynchronously using Celery
- Track execution progress and status
- Store step outputs and activity logs in Cosmos DB
- Monitor and manage running executions

## Architecture

### Components

1. **Execution API** (`/api/executions`) - REST endpoints for batch management
2. **Celery Tasks** - Asynchronous processing workers
3. **Redis** - Message broker and result backend
4. **Cosmos DB** - Storage for execution state and results

### Data Flow

```
Client Request → API → Celery Task → Pipeline Execution → Results Storage
     ↓                    ↓               ↓                ↓
   Batch Created    → Task Queued → Documents Processed → DB Updated
```

## Data Models

### BatchExecution
Tracks the overall batch execution state:
- Pipeline instance reference
- Document list
- Status (pending, running, completed, failed, cancelled)
- Progress metrics
- Celery task ID for tracking

### ActivityLog
Records all activities and events:
- Activity type (batch_started, step_completed, document_processed, etc.)
- Timestamps and duration
- Error messages
- Detailed metadata

### StepOutput
Stores output from each pipeline step:
- Step-specific data and results
- Processing metrics
- Error information

## API Endpoints

### Create Batch Execution
```http
POST /api/executions/
Content-Type: application/json

{
  "pipeline_instance_id": "pipeline_123",
  "documents": [
    {
      "container_name": "documents",
      "blob_name": "document1.pdf",
      "url": "https://storage.../document1.pdf",
      "content_type": "application/pdf",
      "size_bytes": 1024000
    }
  ],
  "batch_name": "Q1 Reports Processing",
  "priority": 1,
  "metadata": {
    "department": "finance",
    "quarter": "Q1"
  }
}
```

### Start Execution
```http
POST /api/executions/{batch_id}/start
```

### Get Status
```http
GET /api/executions/{batch_id}/status
```

Response:
```json
{
  "batch_id": "batch_20241201_143022_5_docs",
  "status": "running",
  "progress": 60.0,
  "total_documents": 5,
  "completed_documents": 3,
  "failed_documents": 0,
  "started_at": "2024-12-01T14:30:22Z",
  "current_step": "pdf_text_extractor",
  "recent_activities": [...]
}
```

### List Executions
```http
GET /api/executions/
GET /api/executions/?status=running
GET /api/executions/?pipeline_id=pipeline_123
```

### Cancel Execution
```http
DELETE /api/executions/{batch_id}
```

### Get Activities
```http
GET /api/executions/{batch_id}/activities?limit=50
```

### Get Step Outputs
```http
GET /api/executions/{batch_id}/step-outputs
GET /api/executions/{batch_id}/step-outputs?step_name=pdf_extractor
GET /api/executions/{batch_id}/step-outputs?document_id=doc1.pdf
```

### Retry Failed Execution
```http
POST /api/executions/{batch_id}/retry
```

## Setup and Deployment

### Prerequisites

1. **Redis Server** - For Celery message broker
2. **Cosmos DB** - For data storage
3. **Azure Blob Storage** - For document storage

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis (using Docker Compose):
```bash
cd backend-app
docker-compose up redis -d
```

3. Set environment variables:
```bash
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export COSMOS_ENDPOINT="your-cosmos-endpoint"
export COSMOS_KEY="your-cosmos-key"
```

4. Start Celery worker:
```bash
cd backend-app
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

5. Start FastAPI server:
```bash
cd backend-app
uvicorn app.main:app --reload
```

### Optional Monitoring

Start Flower for Celery monitoring:
```bash
docker-compose --profile monitoring up flower -d
# Access at http://localhost:5555
```

Start Redis Commander for Redis management:
```bash
docker-compose --profile ui up redis-commander -d
# Access at http://localhost:8081
```

## Configuration

### Celery Settings

Configure in `app/celery_app.py`:
- Broker URL (Redis)
- Result backend (Redis)
- Task queues and routing
- Worker settings

### Queue Configuration

Two main queues:
- `pipeline_execution` - For batch processing tasks
- `document_processing` - For individual document tasks
- `default` - For other tasks

### Cosmos DB Containers

New containers created:
- `batch_executions` - Batch execution records
- `activities` - Activity logs
- `step_outputs` - Step processing results

## Usage Examples

### Basic Batch Processing

```python
import httpx

# Create batch
batch_request = {
    "pipeline_instance_id": "pipeline_123",
    "documents": [
        {
            "container_name": "documents",
            "blob_name": "report1.pdf",
            "url": "https://storage.../report1.pdf"
        },
        {
            "container_name": "documents", 
            "blob_name": "report2.pdf",
            "url": "https://storage.../report2.pdf"
        }
    ],
    "batch_name": "Monthly Reports"
}

# Submit batch
response = httpx.post("http://localhost:8000/api/executions/", json=batch_request)
batch = response.json()
batch_id = batch["id"]

# Start execution
httpx.post(f"http://localhost:8000/api/executions/{batch_id}/start")

# Monitor progress
while True:
    status = httpx.get(f"http://localhost:8000/api/executions/{batch_id}/status").json()
    print(f"Progress: {status['progress']}%")
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(5)

# Get results
outputs = httpx.get(f"http://localhost:8000/api/executions/{batch_id}/step-outputs").json()
```

### Bulk Document Processing

```python
# Process large document set
documents = []
for i in range(100):
    documents.append({
        "container_name": "legal-docs",
        "blob_name": f"contract_{i:03d}.pdf",
        "url": f"https://storage.../contract_{i:03d}.pdf"
    })

batch_request = {
    "pipeline_instance_id": "legal_document_pipeline",
    "documents": documents,
    "batch_name": "Legal Contract Analysis",
    "priority": 2,
    "metadata": {
        "department": "legal",
        "project": "contract_review_2024"
    }
}

# Submit and start
response = httpx.post("http://localhost:8000/api/executions/", json=batch_request)
batch_id = response.json()["id"]
httpx.post(f"http://localhost:8000/api/executions/{batch_id}/start")
```

## Error Handling

### Batch-Level Errors
- Invalid pipeline instance
- Document access failures
- Celery worker unavailability

### Document-Level Errors
- Individual document processing failures
- Step execution errors
- Service unavailability

### Recovery Mechanisms
- Automatic retry for transient failures
- Manual retry for failed batches
- Detailed error logging and tracking

## Monitoring and Observability

### Metrics Available
- Batch execution statistics
- Document processing rates
- Step execution times
- Error rates and types

### Logging
- Structured activity logs
- Step-by-step execution traces
- Error details and stack traces

### Dashboards
- Flower for Celery monitoring
- Custom metrics via activity logs
- Real-time status updates

## Performance Considerations

### Scaling Workers
```bash
# Multiple workers
celery -A app.celery_app worker --concurrency=8 --loglevel=info

# Multiple worker processes
celery multi start 4 -A app.celery_app --loglevel=info
```

### Queue Management
- Separate queues for different workloads
- Priority-based task routing
- Resource isolation

### Memory Management
- Limit tasks per worker child process
- Monitor memory usage
- Implement result expiration

### Database Optimization
- Efficient indexing on query fields
- Batch operations for bulk inserts
- Connection pooling

## Security Considerations

### Authentication
- API endpoints should be protected
- Service-to-service authentication
- Document access permissions

### Data Protection
- Secure credential storage
- Encrypted data transmission
- Audit logging

### Network Security
- Redis authentication
- Network isolation
- TLS encryption

## Troubleshooting

### Common Issues

1. **Celery worker not processing tasks**
   - Check Redis connectivity
   - Verify worker is running
   - Check queue configuration

2. **Documents not found**
   - Verify blob storage credentials
   - Check container and blob names
   - Validate document URLs

3. **Pipeline execution failures**
   - Check pipeline configuration
   - Verify service availability
   - Review step dependencies

### Debug Commands

```bash
# Check Celery status
celery -A app.celery_app status

# Monitor queue
celery -A app.celery_app monitor

# Inspect tasks
celery -A app.celery_app inspect active

# Purge queue
celery -A app.celery_app purge
```

### Log Analysis

Review logs for:
- Task execution traces
- Error patterns
- Performance bottlenecks
- Resource utilization

## Future Enhancements

### Planned Features
- Parallel document processing
- Resume interrupted executions
- Batch scheduling
- Resource allocation controls
- Advanced retry policies
- Multi-tenant isolation

### Integration Opportunities
- Event-driven triggers
- Webhook notifications
- External monitoring systems
- Custom result processors
