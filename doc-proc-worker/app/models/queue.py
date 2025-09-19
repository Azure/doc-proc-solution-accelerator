from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

class QueueMessageType(str, Enum):
    """Types of messages that can be sent to the queue"""
    BATCH_EXECUTION_REQUEST = "batch_execution_request"
    BATCH_RETRY_REQUEST = "batch_retry_request"
    BATCH_CANCEL_REQUEST = "batch_cancel_request"


class QueueBatchExecutionRequest(BaseModel):
    """Message format for batch execution requests in the queue"""
    message_type: QueueMessageType = Field(default=QueueMessageType.BATCH_EXECUTION_REQUEST)
    pipeline_name: str = Field(..., description="Name of the pipeline to execute")
    documents: List[Dict[str, Any]] = Field(..., description="List of documents to process")
    batch_id: Optional[str] = Field(None, description="Optional ID for the batch")
    priority: int = Field(default=0, description="Execution priority (higher = more priority)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Queue-specific fields
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="When message was submitted")
    requested_by: Optional[str] = Field(None, description="User or system that requested the batch")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    
    # Retry configuration
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay_seconds: int = Field(default=60, description="Delay between retries in seconds")


class QueueBatchRetryRequest(BaseModel):
    """Message format for batch retry requests"""
    message_type: QueueMessageType = Field(default=QueueMessageType.BATCH_RETRY_REQUEST)
    batch_id: str = Field(..., description="ID of the batch to retry")
    retry_attempt: int = Field(default=1, description="Current retry attempt number")
    original_error: Optional[str] = Field(None, description="Original error that caused the retry")
    
    # Queue-specific fields
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    requested_by: Optional[str] = Field(None)
    correlation_id: Optional[str] = Field(None)


class QueueBatchCancelRequest(BaseModel):
    """Message format for batch cancellation requests"""
    message_type: QueueMessageType = Field(default=QueueMessageType.BATCH_CANCEL_REQUEST)
    batch_id: str = Field(..., description="ID of the batch to cancel")
    reason: Optional[str] = Field(None, description="Reason for cancellation")
    
    # Queue-specific fields
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    requested_by: Optional[str] = Field(None)
    correlation_id: Optional[str] = Field(None)


class QueueMessageWrapper(BaseModel):
    """Wrapper for queue messages with metadata"""
    message_id: str = Field(..., description="Queue message ID")
    message_type: QueueMessageType = Field(..., description="Type of message")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    
    # Processing metadata
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processing_started_at: Optional[datetime] = Field(None)
    processing_completed_at: Optional[datetime] = Field(None)
    processing_error: Optional[str] = Field(None)
    retry_count: int = Field(default=0)
    
    def get_typed_payload(self):
        """Get the typed payload based on message type"""
        if self.message_type == QueueMessageType.BATCH_EXECUTION_REQUEST:
            return QueueBatchExecutionRequest(**self.payload)
        elif self.message_type == QueueMessageType.BATCH_RETRY_REQUEST:
            return QueueBatchRetryRequest(**self.payload)
        elif self.message_type == QueueMessageType.BATCH_CANCEL_REQUEST:
            return QueueBatchCancelRequest(**self.payload)
        else:
            raise ValueError(f"Unknown message type: {self.message_type}")


class QueueWorkerStats(BaseModel):
    """Statistics for the queue worker"""
    worker_id: str
    started_at: datetime
    last_activity_at: datetime
    
    # Message processing stats
    total_messages_processed: int = 0
    successful_messages: int = 0
    failed_messages: int = 0
    retried_messages: int = 0
    
    # Current state
    is_running: bool = True
    current_message_id: Optional[str] = None
    processing_since: Optional[datetime] = None
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    messages_per_minute: float = 0.0
    
    def update_processing_stats(self, processing_time_ms: float, success: bool):
        """Update processing statistics"""
        self.total_messages_processed += 1
        self.last_activity_at = datetime.utcnow()
        
        if success:
            self.successful_messages += 1
        else:
            self.failed_messages += 1
        
        # Update average processing time
        if self.total_messages_processed == 1:
            self.average_processing_time_ms = processing_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.average_processing_time_ms = (
                alpha * processing_time_ms + 
                (1 - alpha) * self.average_processing_time_ms
            )
        
        # Update messages per minute (simple rate calculation)
        duration_minutes = (self.last_activity_at - self.started_at).total_seconds() / 60
        if duration_minutes > 0:
            self.messages_per_minute = self.total_messages_processed / duration_minutes
