# Azure Storage Queue Worker - Testing Scripts

This directory contains scripts for testing the Azure Storage Queue worker functionality.

## Overview

The queue worker system consists of:
- **Queue Worker** (`queue_worker.py`): Continuously polls Azure Storage Queue for batch execution requests
- **Test Scripts**: Various utilities to send test messages and manage the queue

## Prerequisites

1. **Azure Storage Account**: Configure the storage account URL and credentials in `.env`
2. **Redis**: Running Redis instance for Celery (configured in `.env`)
3. **Cosmos DB**: Database for storing execution metadata (configured in `.env`)

## Configuration

Update your `.env` file with the Azure Storage Queue settings:

```bash
# Azure Storage Queue settings
STORAGE_ACCOUNT_WORKER_QUEUE_URL=https://yourstorageaccount.queue.core.windows.net/
STORAGE_WORKER_QUEUE_NAME=docproc-execution-requests
```

## Running the Queue Worker

Start the queue worker to begin processing messages:

```bash
python run_queue_worker.py
```

The worker will:
- Connect to Azure Storage Queue
- Poll for messages every 5 seconds
- Process batch execution requests by submitting them to Celery
- Handle retries and error scenarios

## Testing Scripts

### 1. Quick Queue Test (`quick_queue_test.py`)

Sends a few sample messages quickly for immediate testing:

```bash
python quick_queue_test.py
```

This will send 3 test batch execution requests with different pipelines and priorities.

### 2. Interactive Test Sender (`send_test_messages.py`)

Full-featured interactive script for sending various types of messages:

```bash
python send_test_messages.py
```

Features:
- Interactive menu system
- Send batch execution requests
- Send retry/cancel requests
- Peek at queue messages
- Get queue statistics
- Bulk message sending

You can also use it in batch mode:
```bash
python send_test_messages.py send 5    # Send 5 test messages
python send_test_messages.py peek 10   # Peek at 10 messages
python send_test_messages.py stats     # Get queue stats
```

### 3. Queue Manager (`queue_manager.py`)

Utility for managing the queue:

```bash
# Peek at messages
python queue_manager.py peek --count 10

# Get queue statistics
python queue_manager.py stats

# Delete specific number of messages
python queue_manager.py delete --count 5

# Clear entire queue (with confirmation)
python queue_manager.py clear
```

## Message Types

The queue worker processes three types of messages:

### 1. Batch Execution Request
```json
{
  "message_type": "batch_execution_request",
  "pipeline_instance_id": "entity_extraction_pipeline_001",
  "documents": [
    {
      "container_name": "documents",
      "blob_name": "document1.pdf",
      "url": "https://storage.blob.core.windows.net/documents/document1.pdf",
      "content_type": "application/pdf",
      "size_bytes": 2048
    }
  ],
  "batch_name": "My Test Batch",
  "priority": 1,
  "metadata": {},
  "submitted_at": "2025-09-03T10:30:00Z",
  "requested_by": "user@example.com",
  "correlation_id": "test_12345"
}
```

### 2. Batch Retry Request
```json
{
  "message_type": "batch_retry_request",
  "batch_id": "batch_20250903_103000_3_docs",
  "retry_attempt": 1,
  "original_error": "Pipeline execution failed",
  "submitted_at": "2025-09-03T10:35:00Z",
  "requested_by": "system",
  "correlation_id": "retry_12345"
}
```

### 3. Batch Cancel Request
```json
{
  "message_type": "batch_cancel_request",
  "batch_id": "batch_20250903_103000_3_docs",
  "reason": "User requested cancellation",
  "submitted_at": "2025-09-03T10:40:00Z",
  "requested_by": "user@example.com",
  "correlation_id": "cancel_12345"
}
```

## Workflow

1. **Send Messages**: Use test scripts to send batch execution requests to the queue
2. **Queue Worker**: Polls the queue and processes messages
3. **Celery Integration**: Worker submits batch executions to Celery tasks
4. **Monitoring**: Use queue manager to monitor message flow and statistics

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify Azure Storage credentials and network connectivity
2. **Queue Not Found**: The worker will create the queue automatically if it doesn't exist
3. **Message Parsing Errors**: Check that messages follow the expected JSON schema
4. **Celery Not Running**: Ensure Celery worker is running separately (`python run_celery.py`)

### Logging

All scripts include detailed logging. Check console output and log files for debugging information.

### Monitoring

- **Queue Statistics**: Use `queue_manager.py stats` to check message counts
- **Worker Status**: Monitor the queue worker output for processing status
- **Celery Monitoring**: Use Flower or Celery monitoring tools for task status

## Examples

### Basic Test Flow

1. Start the queue worker:
   ```bash
   python run_queue_worker.py
   ```

2. In another terminal, send test messages:
   ```bash
   python quick_queue_test.py
   ```

3. Monitor the queue worker output to see messages being processed

4. Check queue status:
   ```bash
   python queue_manager.py stats
   ```

### Advanced Testing

1. Send multiple messages with different priorities:
   ```bash
   python send_test_messages.py
   # Choose option 6 for bulk sending
   ```

2. Peek at queue contents:
   ```bash
   python queue_manager.py peek --count 20
   ```

3. Test retry scenarios by sending retry requests for existing batch IDs

4. Test cancellation by sending cancel requests

This testing framework provides comprehensive coverage for validating the queue worker functionality and integration with the broader document processing system.
