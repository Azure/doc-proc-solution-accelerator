from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .common import BaseDoc


class BatchStatus(str, Enum):
    """Enum for batch execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActivityType(str, Enum):
    """Enum for activity types"""
    BATCH_CREATED = "batch_created"
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
    BATCH_FAILED = "batch_failed"
    BATCH_CANCELLED = "batch_cancelled"
    BATCH_RETRY = "batch_retry"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"


class DocumentReference(BaseModel):
    """Reference to a document in Azure Blob Storage"""
    container_name: str = Field(..., description="Azure Blob container name")
    blob_name: str = Field(..., description="Blob name/path")
    url: Optional[str] = Field(None, description="Full URL to the blob")
    content_type: Optional[str] = Field(None, description="Document content type")
    size_bytes: Optional[int] = Field(None, description="Document size in bytes")


class BatchExecutionRequest(BaseModel):
    """Request model for batch execution"""
    pipeline_name: str = Field(..., description="Name of the pipeline to execute")
    documents: List[Dict[str, Any]] = Field(..., description="List of documents to process")
    batch_name: Optional[str] = Field(None, description="Optional name for the batch")
    priority: int = Field(default=0, description="Execution priority (higher = more priority)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StepOutput(BaseModel):
    """Model for step execution output"""
    step_name: str
    step_instance_id: str
    document_id: str
    output_data: Dict[str, Any] = Field(default_factory=dict)
    summary_data: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BatchExecution(BaseDoc):
    """Model for batch execution tracking"""
    pipeline_name: str = Field(..., description="Name of the pipeline")
    documents: List[Dict[str, Any]] = Field(..., description="Documents in the batch")
    status: BatchStatus = Field(default=BatchStatus.PENDING, description="Current batch status")
    celery_task_id: Optional[str] = Field(None, description="Celery task ID for tracking")
    priority: int = Field(default=0, description="Execution priority")
    
    # Execution statistics
    total_documents: int = Field(default=0, description="Total number of documents")
    completed_documents: int = Field(default=0, description="Number of completed documents")
    failed_documents: int = Field(default=0, description="Number of failed documents")
    
    # Timing information
    submitted_at: Optional[str] = Field(None, description="Batch execution submission time to Celery in utc tz iso-format")
    started_at: Optional[str] = Field(None, description="Batch execution start time in utc tz iso-format")
    completed_at: Optional[str] = Field(None, description="Batch execution completion time in utc tz iso-format")

    # Results and errors
    results: Dict[str, Any] = Field(default_factory=dict, description="Batch execution results")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ActivityLog(BaseDoc):
    """Model for activity logging"""
    batch_execution_id: str = Field(..., description="ID of the related batch execution")
    activity_type: ActivityType = Field(..., description="Type of activity")
    step_name: Optional[str] = Field(None, description="Name of the step (if applicable)")
    document_id: Optional[str] = Field(None, description="Document ID (if applicable)")
    
    # Activity details
    details: Dict[str, Any] = Field(default_factory=dict, description="Activity details")
    status: str = Field(..., description="Activity status")
    message: Optional[str] = Field(None, description="Activity message")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Timing
    duration_ms: Optional[int] = Field(None, description="Activity duration in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Activity timestamp")
    
    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BatchExecutionStatus(BaseModel):
    """Status response for batch execution"""
    batch_id: str
    status: BatchStatus
    progress: float = Field(..., description="Progress percentage (0-100)")
    total_documents: int
    completed_documents: int
    failed_documents: int
    current_step: Optional[str] = Field(None, description="Current processing step")
    started_at: Optional[str] = Field(None, description="Start time in ISO format")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time in ISO format")
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list, description="Recent activities")
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    current_step: Optional[str] = None
    recent_activities: List[ActivityLog] = Field(default_factory=list)
