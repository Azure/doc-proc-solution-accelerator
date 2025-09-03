import asyncio
import json
import logging
import signal
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.services.queue_service import AzureQueueService, QueueMessage
from app.services.execution_service import ExecutionService
from app.models.queue_models import (
    QueueMessageWrapper, QueueMessageType, QueueBatchExecutionRequest,
    QueueBatchRetryRequest, QueueBatchCancelRequest, QueueWorkerStats
)
from app.models.execution import BatchExecutionRequest, BatchStatus
from app.tasks import execute_pipeline_batch


logger = logging.getLogger("doc-proc-worker.app.queue_worker")

class QueueWorker:
    """Async worker that processes batch execution requests from Azure Storage Queue"""
    
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.queue_service: AzureQueueService = None
        self.execution_service: ExecutionService = None
        self.stats = QueueWorkerStats(
            worker_id=self.worker_id,
            started_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        
        # Worker configuration
        self.poll_interval_seconds = 5  # How often to check for new messages
        self.max_messages_per_poll = 5  # Max messages to process per poll
        self.message_visibility_timeout = 300  # 5 minutes
        self.max_processing_time = 600  # 10 minutes max per message
        
        # Control flags
        self._shutdown_requested = False
        self._current_message: QueueMessage = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True
    
    async def start(self):
        """Start the queue worker"""
        logger.info(f"Starting queue worker: {self.worker_id}")
        
        try:
            # Initialize services
            await self._initialize_services()
            
            # Main processing loop
            await self._run_processing_loop()
            
        except Exception as e:
            logger.error(f"Fatal error in queue worker: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _initialize_services(self):
        """Initialize required services"""
        logger.info("Initializing services...")
        
        logger.debug("Setting up Azure Queue Service...")
        # Connect to Azure Storage Queue
        self.queue_service = AzureQueueService()
        await self.queue_service.connect()
        
        logger.debug("Setting up Execution Service...")
        self.execution_service = ExecutionService()
        
        logger.info("Services initialized successfully")
    
    async def _run_processing_loop(self):
        """Main processing loop"""
        logger.info("Starting message processing loop...")
        
        while not self._shutdown_requested:
            try:
                # Poll for messages
                messages = await self.queue_service.receive_messages(
                    max_messages=self.max_messages_per_poll,
                    visibility_timeout=self.message_visibility_timeout
                )
                
                if not messages:
                    # No messages available, wait before next poll
                    await asyncio.sleep(self.poll_interval_seconds)
                    continue
                
                # Process messages concurrently
                tasks = [self._process_message(msg) for msg in messages]
                await asyncio.gather(*tasks, return_exceptions=True)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(self.poll_interval_seconds)
        
        logger.info("Processing loop shutdown complete")
    
    async def _process_message(self, message: QueueMessage):
        """Process a single queue message"""
        start_time = datetime.now(timezone.utc)
        processing_time_ms = 0
        success = False
        
        try:
            self._current_message = message
            self.stats.current_message_id = message.id
            self.stats.processing_since = start_time
            
            logger.info(f"Processing message: {message.id}")
            
            # Parse message content
            try:
                message_wrapper = QueueMessageWrapper(
                    message_id=message.id,
                    message_type=message.content.get("message_type"),
                    payload=message.content,
                    received_at=start_time
                )
            except Exception as e:
                logger.error(f"Failed to parse message {message.id}: {e}")
                await self._handle_poison_message(message, str(e))
                return
            
            # Process based on message type
            result = await self._handle_message_by_type(message_wrapper)
            
            if result:
                # Message processed successfully, delete from queue
                await self.queue_service.delete_message(message)
                success = True
                logger.info(f"Successfully processed and deleted message: {message.id}")
            else:
                # Processing failed, handle retry logic
                await self._handle_message_retry(message, message_wrapper)
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            await self._handle_message_error(message, str(e))
        
        finally:
            # Update statistics
            end_time = datetime.now(timezone.utc)
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            self.stats.update_processing_stats(processing_time_ms, success)
            
            # Clear current message tracking
            self._current_message = None
            self.stats.current_message_id = None
            self.stats.processing_since = None
    
    async def _handle_message_by_type(self, wrapper: QueueMessageWrapper) -> bool:
        """Handle message based on its type"""
        try:
            payload = wrapper.get_typed_payload()
            
            if wrapper.message_type == QueueMessageType.BATCH_EXECUTION_REQUEST:
                return await self._handle_batch_execution_request(payload)
            
            elif wrapper.message_type == QueueMessageType.BATCH_RETRY_REQUEST:
                return await self._handle_batch_retry_request(payload)
            
            elif wrapper.message_type == QueueMessageType.BATCH_CANCEL_REQUEST:
                return await self._handle_batch_cancel_request(payload)
            
            else:
                logger.error(f"Unknown message type: {wrapper.message_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling message type {wrapper.message_type}: {e}")
            return False
    
    async def _handle_batch_execution_request(self, request: QueueBatchExecutionRequest) -> bool:
        """Handle batch execution request"""
        try:
            logger.info(f"Creating batch execution for pipeline: {request.pipeline_instance_id}")
            
            # Convert to BatchExecutionRequest
            batch_request = BatchExecutionRequest(
                pipeline_instance_id=request.pipeline_instance_id,
                documents=request.documents,
                batch_name=request.batch_name,
                priority=request.priority,
                metadata={
                    **request.metadata,
                    "queue_worker_id": self.worker_id,
                    "submitted_at": request.submitted_at,
                    "correlation_id": request.correlation_id,
                    "requested_by": request.requested_by
                }
            )
            
            # Create batch execution
            batch = await self.execution_service.create_batch_execution(batch_request)
            
            # Submit to Celery for processing
            task = execute_pipeline_batch.delay(batch.id)
            
            # Update batch with task ID
            await self.execution_service.update_batch_status(
                batch.id,
                BatchStatus.RUNNING,
                celery_task_id=task.id,
                started_at=datetime.now(timezone.utc).isoformat()
            )
            
            logger.info(f"Successfully submitted batch {batch.id} to Celery with task ID: {task.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle batch execution request: {e}")
            return False
    
    async def _handle_batch_retry_request(self, request: QueueBatchRetryRequest) -> bool:
        """Handle batch retry request"""
        try:
            logger.info(f"Retrying batch execution: {request.batch_id}")
            
            # Get existing batch
            batch = await self.execution_service.get_batch_execution(request.batch_id)
            if not batch:
                logger.error(f"Batch not found for retry: {request.batch_id}")
                return True  # Consider this "handled" since batch doesn't exist
            
            # Check if batch is in a retryable state
            if batch.status not in [BatchStatus.FAILED, BatchStatus.CANCELLED]:
                logger.warning(f"Batch {request.batch_id} not in retryable state: {batch.status}")
                return True
            
            # Submit retry to Celery
            task = execute_pipeline_batch.delay(batch.id)
            
            # Update batch status
            await self.execution_service.update_batch_status(
                batch.id,
                BatchStatus.RUNNING,
                celery_task_id=task.id,
                started_at=datetime.utcnow()
            )
            
            # Log retry activity
            await self.execution_service.log_activity(
                batch_execution_id=batch.id,
                activity_type="BATCH_RETRY",
                status="retrying",
                message=f"Batch retry attempt {request.retry_attempt}",
                details={
                    "retry_attempt": request.retry_attempt,
                    "original_error": request.original_error,
                    "task_id": task.id
                }
            )
            
            logger.info(f"Successfully retried batch {batch.id} with task ID: {task.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle batch retry request: {e}")
            return False
    
    async def _handle_batch_cancel_request(self, request: QueueBatchCancelRequest) -> bool:
        """Handle batch cancellation request"""
        try:
            logger.info(f"Cancelling batch execution: {request.batch_id}")
            
            # Get existing batch
            batch = await self.execution_service.get_batch_execution(request.batch_id)
            if not batch:
                logger.error(f"Batch not found for cancellation: {request.batch_id}")
                return True  # Consider this "handled" since batch doesn't exist
            
            # Check if batch can be cancelled
            if batch.status not in [BatchStatus.PENDING, BatchStatus.RUNNING]:
                logger.warning(f"Batch {request.batch_id} cannot be cancelled in state: {batch.status}")
                return True
            
            # Cancel Celery task if running
            if batch.celery_task_id:
                from celery import current_app
                current_app.control.revoke(batch.celery_task_id, terminate=True)
            
            # Update batch status
            await self.execution_service.update_batch_status(
                batch.id,
                BatchStatus.CANCELLED,
                completed_at=datetime.utcnow()
            )
            
            # Log cancellation activity
            await self.execution_service.log_activity(
                batch_execution_id=batch.id,
                activity_type="BATCH_CANCELLED",
                status="cancelled",
                message=f"Batch cancelled via queue request",
                details={
                    "reason": request.reason,
                    "requested_by": request.requested_by
                }
            )
            
            logger.info(f"Successfully cancelled batch {batch.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle batch cancel request: {e}")
            return False
    
    async def _handle_message_retry(self, message: QueueMessage, wrapper: QueueMessageWrapper):
        """Handle message retry logic"""
        max_retries = 3
        
        if message.dequeue_count >= max_retries:
            logger.error(f"Message {message.id} exceeded max retries ({max_retries}), moving to poison queue")
            await self._handle_poison_message(message, "Max retries exceeded")
        else:
            # Update visibility to retry later
            retry_delay = min(60 * (2 ** message.dequeue_count), 300)  # Exponential backoff, max 5 minutes
            logger.info(f"Retrying message {message.id} in {retry_delay} seconds (attempt {message.dequeue_count + 1})")
            
            await self.queue_service.update_message(
                message,
                wrapper.payload,
                visibility_timeout=retry_delay
            )
    
    async def _handle_message_error(self, message: QueueMessage, error: str):
        """Handle message processing error"""
        logger.error(f"Message {message.id} processing error: {error}")
        
        # For now, just log the error and let retry logic handle it
        # In production, you might want to update the message with error info
    
    async def _handle_poison_message(self, message: QueueMessage, error: str):
        """Handle poison messages that cannot be processed"""
        logger.error(f"Handling poison message {message.id}: {error}")
        
        # In production, you would typically:
        # 1. Move message to a poison queue for manual inspection
        # 2. Log to a dead letter queue
        # 3. Send alerts
        
        # For now, just delete the message to prevent infinite retries
        await self.queue_service.delete_message(message)
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        
        try:
            if self.queue_service:
                await self.queue_service.disconnect()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        self.stats.is_running = False
        logger.info("Cleanup complete")
    
    def get_stats(self) -> QueueWorkerStats:
        """Get current worker statistics"""
        return self.stats
