import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.dependencies import get_execution_manager, get_queue_proxy
from app.proxy.queue import StorageQueue, QueueMessage
from app.managers.execution_manager import ExecutionManager
from app.models.queue import (
    QueueMessageWrapper, QueueMessageType, QueueBatchExecutionRequest,
    QueueBatchRetryRequest, QueueBatchCancelRequest, QueueWorkerStats
)
from app.models.execution import BatchExecutionRequest, BatchStatus, ActivityType


class QueueWorker:
    """Async worker that processes batch execution requests from Azure Storage Queue"""
    
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.queue_proxy: Optional[StorageQueue] = None
        self.execution_manager: Optional[ExecutionManager] = None
        self.stats = QueueWorkerStats(
            worker_id=self.worker_id,
            started_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        
        # Worker configuration
        # TODO: make these configurable via settings or constructor
        self.poll_interval_seconds = 5  # How often to check for new messages
        self.max_messages_per_poll = 1  # Max messages to process per poll
        self.message_visibility_timeout = 24 * 60 * 60  # 24 hours
        self.max_processing_time = 600  # 10 minutes max per message
        
        # Control flags
        self._shutdown_requested = False
        self._current_message: Optional[QueueMessage] = None

        # Logging configuration
        self.logger = logging.getLogger(f"doc-proc-worker.app.{self.worker_id}")

    
    async def start(self):
        """Start the queue worker"""
        self.logger.info(f"Starting queue worker: {self.worker_id}")
        
        try:
            # Initialize services
            await self._initialize_services()
            
            if not self.queue_proxy or not self.execution_manager:
                raise RuntimeError("Failed to initialize required services")
            
            # Main processing loop
            await self._run_processing_loop()
            
        except Exception as e:
            self.logger.error(f"Fatal error in queue worker: {e}", exc_info=True, stack_info=True)
            raise
        finally:
            await self._cleanup()
    
    
    async def _initialize_services(self):
        """Initialize required services"""
        self.logger.info("Initializing services...")

        self.logger.debug("Setting up Azure Storage Queue Service...")
        # Connect to Azure Storage Queue
        self.queue_proxy = get_queue_proxy()
        await self.queue_proxy.connect()

        self.logger.debug("Setting up Execution Service...")
        self.execution_manager = get_execution_manager()

        self.logger.info("Services initialized successfully")


    async def _run_processing_loop(self):
        """Main processing loop"""
        self.logger.info("Starting message processing loop...")

        if not self.queue_proxy:
            raise RuntimeError("Queue service not initialized")
            
        while not self._shutdown_requested:
            try:
                # Poll for messages
                messages = await self.queue_proxy.receive_messages(
                    max_messages=self.max_messages_per_poll,
                    visibility_timeout=self.message_visibility_timeout
                )
                
                if not messages:
                    # No messages available, wait before next poll
                    # Use a shorter sleep with checks for shutdown to be more responsive
                    for _ in range(self.poll_interval_seconds):
                        if self._shutdown_requested:
                            break
                        try:
                            await asyncio.sleep(1)
                        except asyncio.CancelledError:
                            self.logger.debug("Sleep cancelled during shutdown")
                            self._shutdown_requested = True
                            break
                    continue
                
                # Process messages concurrently
                tasks = [self._process_message(msg) for msg in messages]
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    self.logger.debug("Message processing cancelled during shutdown")
                    self._shutdown_requested = True
                    break
                
            except asyncio.CancelledError:
                self.logger.debug("Processing loop cancelled during shutdown")
                self._shutdown_requested = True
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                # Also handle cancellation in error case
                try:
                    await asyncio.sleep(self.poll_interval_seconds)
                except asyncio.CancelledError:
                    self.logger.debug("Error recovery sleep cancelled during shutdown")
                    self._shutdown_requested = True
                    break

        self.logger.info("Processing loop shutdown complete")


    async def _process_message(self, message: QueueMessage):
        """Process a single queue message"""
        start_time = datetime.now(timezone.utc)
        processing_time_ms = 0
        success = False
        
        try:
            self._current_message = message
            self.stats.current_message_id = message.id
            self.stats.processing_since = start_time

            self.logger.info(f"Processing message: {message.id}")

            # Parse message content
            try:
                message_type = message.content.get("message_type")
                if not message_type or not isinstance(message_type, str) or message_type not in [e.value for e in QueueMessageType]:
                    raise ValueError("Invalid or missing message_type in queue message.")
                
                message_wrapper = QueueMessageWrapper(
                    message_id=message.id,
                    message_type=QueueMessageType(message_type),
                    payload=message.content,
                    received_at=start_time,
                    processing_started_at=None,
                    processing_completed_at=None,
                    processing_error=None
                )
            except Exception as e:
                self.logger.error(f"Failed to parse message {message.id}: {e}")
                await self._handle_poison_message(message, str(e))
                return
            
            # Process based on message type
            result = await self._handle_message_by_type(message_wrapper)
            
            if not self.queue_proxy:
                raise RuntimeError("Queue service not initialized")
            
            if result: 
                # Message processed successfully, delete from queue
                await self.queue_proxy.delete_message(message)
                success = True
                self.logger.info(f"Successfully processed and deleted message: {message.id}")
            else:
                # Processing failed, handle retry logic
                await self._handle_message_retry(message, message_wrapper)
            
        except Exception as e:
            self.logger.error(f"Error processing message {message.id}: {e}")
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
                if isinstance(payload, QueueBatchExecutionRequest):
                    return await self._handle_batch_execution_request(payload)
                self.logger.error("Invalid payload for BATCH_EXECUTION_REQUEST")
                return False
            
            elif wrapper.message_type == QueueMessageType.BATCH_RETRY_REQUEST:
                if isinstance(payload, QueueBatchRetryRequest):
                    return await self._handle_batch_retry_request(payload)
                self.logger.error("Invalid payload for BATCH_RETRY_REQUEST")
                return False

            elif wrapper.message_type == QueueMessageType.BATCH_CANCEL_REQUEST:
                if isinstance(payload, QueueBatchCancelRequest):
                    return await self._handle_batch_cancel_request(payload)
                self.logger.error("Invalid payload for BATCH_CANCEL_REQUEST")
                return False

            else:
                self.logger.error(f"Unknown message type: {wrapper.message_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error handling message type {wrapper.message_type}: {e}")
            return False
    
    
    async def _handle_batch_execution_request(self, request: QueueBatchExecutionRequest) -> bool:
        """Handle batch execution request"""
        try:
            self.logger.debug(f"Creating batch execution for pipeline: {request.pipeline_name} and batch request: {request.batch_id}")
            
            # Convert to BatchExecutionRequest
            batch_request = BatchExecutionRequest(
                pipeline_name=request.pipeline_name,
                vault_id=request.vault_id,
                documents=request.documents,
                source_batch_id=request.batch_id,
                metadata={
                    **request.metadata,
                    "queue_worker_id": self.worker_id,
                    "submitted_at": request.submitted_at,
                    "correlation_id": request.correlation_id,
                    "requested_by": request.requested_by
                }
            )
            
            if not self.execution_manager:
                raise RuntimeError("Execution manager not initialized")
            
            # Submit batch for execution
            result = await self.execution_manager.execute_batch(batch_execution_request=batch_request)

            self.logger.debug(f"Batch execution result: {result}")

            self.logger.debug(f"Successfully processed source batch {request.batch_id}.")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle batch execution request: {e}")
            self.logger.exception(e)
            return False
    
    
    async def _handle_batch_retry_request(self, request: QueueBatchRetryRequest) -> bool:
        """Handle batch retry request"""
        try:
            self.logger.info(f"Retrying batch execution: {request.batch_id}")
            
            if not self.execution_manager:
                raise RuntimeError("Execution manager not initialized")
            
            # Get existing batch
            batch = await self.execution_manager.get_batch_execution(request.batch_id)
            if not batch:
                self.logger.error(f"Batch not found for retry: {request.batch_id}")
                return True  # Consider this "handled" since batch doesn't exist
            
            # Check if batch is in a retryable state
            if batch.status not in [BatchStatus.FAILED, BatchStatus.CANCELLED]:
                self.logger.warning(f"Batch {request.batch_id} not in retryable state: {batch.status}")
                return True
            
            # Submit retry to Celery
            task = execute_pipeline_batch.delay(batch.id)
            
            # Update batch status
            await self.execution_manager.update_batch_status(
                batch.id,
                BatchStatus.RUNNING,
                celery_task_id=task.id,
                started_at=datetime.now(timezone.utc).isoformat()
            )
            
            # Log retry activity
            await self.execution_manager.log_activity(
                batch_execution_id=batch.id,
                activity_type=ActivityType.BATCH_RETRY,
                status="retrying",
                message=f"Batch retry attempt {request.retry_attempt}",
                details={
                    "retry_attempt": request.retry_attempt,
                    "original_error": request.original_error,
                    "task_id": task.id
                }
            )
            
            self.logger.info(f"Successfully retried batch {batch.id} with task ID: {task.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle batch retry request: {e}")
            return False
    
    
    async def _handle_batch_cancel_request(self, request: QueueBatchCancelRequest) -> bool:
        """Handle batch cancellation request"""
        try:
            self.logger.info(f"Cancelling batch execution: {request.batch_id}")
            
            if not self.execution_manager:
                raise RuntimeError("Execution manager not initialized")
            
            # Get existing batch
            batch = await self.execution_manager.get_batch_execution(request.batch_id)
            if not batch:
                self.logger.error(f"Batch not found for cancellation: {request.batch_id}")
                return True  # Consider this "handled" since batch doesn't exist
            
            # Check if batch can be cancelled
            if batch.status not in [BatchStatus.PENDING, BatchStatus.RUNNING]:
                self.logger.warning(f"Batch {request.batch_id} cannot be cancelled in state: {batch.status}")
                return True
            
            # Cancel Celery task if running
            if batch.celery_task_id:
                from celery import current_app
                current_app.control.revoke(batch.celery_task_id, terminate=True)
            
            # Update batch status
            await self.execution_manager.update_batch_status(
                batch.id,
                BatchStatus.CANCELLED,
                completed_at=datetime.utcnow()
            )
            
            # Log cancellation activity
            await self.execution_manager.log_activity(
                batch_execution_id=batch.id,
                activity_type=ActivityType.BATCH_CANCELLED,
                status="cancelled",
                message=f"Batch cancelled via queue request",
                details={
                    "reason": request.reason,
                    "requested_by": request.requested_by
                }
            )

            self.logger.info(f"Successfully cancelled batch {batch.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle batch cancel request: {e}")
            return False
    
    
    async def _handle_message_retry(self, message: QueueMessage, wrapper: QueueMessageWrapper):
        """Handle message retry logic"""
        max_retries = 3
        
        if message.dequeue_count >= max_retries:
            self.logger.error(f"Message {message.id} exceeded max retries ({max_retries}), moving to poison queue")
            await self._handle_poison_message(message, "Max retries exceeded")
        else:
            # Update visibility to retry later
            retry_delay = min(10 * (2 ** message.dequeue_count), 60)  # Exponential backoff, max 1 minute
            self.logger.info(f"Retrying message {message.id} in {retry_delay} seconds (attempt {message.dequeue_count + 1})")
            
            if not self.queue_proxy:
                raise RuntimeError("Queue service not initialized")
            
            await self.queue_proxy.update_message(
                message,
                wrapper.payload,
                visibility_timeout=retry_delay
            )
    
    
    async def _handle_message_error(self, message: QueueMessage, error: str):
        """Handle message processing error"""
        self.logger.error(f"Message {message.id} processing error: {error}")
        
        # For now, just log the error and let retry logic handle it
        # In production, you might want to update the message with error info
    
    
    async def _handle_poison_message(self, message: QueueMessage, error: str):
        """Handle poison messages that cannot be processed"""
        self.logger.error(f"Handling poison message {message.id}: {error}")
        
        # In production, you would typically:
        # 1. Move message to a poison queue for manual inspection
        # 2. Log to a dead letter queue
        # 3. Send alerts
        
        if not self.queue_proxy:
                raise RuntimeError("Queue service not initialized")
        
        # For now, just delete the message to prevent infinite retries
        await self.queue_proxy.delete_message(message)
    
    
    async def _cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")

        try:
            if self.queue_proxy:
                await self.queue_proxy.disconnect()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        self.stats.is_running = False
        self.logger.info("Cleanup complete")


    def get_stats(self) -> QueueWorkerStats:
        """Get current worker statistics"""
        return self.stats
