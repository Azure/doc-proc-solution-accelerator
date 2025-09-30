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


class DocumentExecutionStatus(BaseModel):
    """Model for document execution status"""
    document_id: str = Field(..., description="ID of the document")
    batch_id: str = Field(..., description="ID of the batch execution where the document was processed")
    batch_status: Optional[str] = Field(None, description="Current status of the batch execution")
    pipeline_execution_id: Optional[str] = Field(None, description="ID of the pipeline execution")
    pipeline_name: Optional[str] = Field(None, description="Name of the pipeline")
    batch_submitted_at: Optional[datetime] = Field(None, description="Submission time of the batch execution")
    batch_started_at: Optional[datetime] = Field(None, description="Start time of the batch execution")
    batch_completed_at: Optional[datetime] = Field(None, description="Completion time of the batch execution")
    batch_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata associated with the batch execution")
    document: Optional[Dict[str, Any]] = Field(None, description="Document details and status")


class DocumentReference(BaseModel):
    """Reference to a document in Azure Blob Storage"""
    container_name: str = Field(..., description="Azure Blob container name")
    blob_name: str = Field(..., description="Blob name/path")
    url: Optional[str] = Field(None, description="Full URL to the blob")
    content_type: Optional[str] = Field(None, description="Document content type")
    size_bytes: Optional[int] = Field(None, description="Document size in bytes")



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



class BatchExecution(BaseModel):
    """Batch execution model retrieved from the database"""
    id: str = Field(..., description="Unique id, used as partition key")
    created_at: str = Field(..., description="Created time in utc tz iso-format")
    updated_at: str = Field(..., description="Updated time in utc tz iso-format")
    pipeline_name: str = Field(..., description="Name of the pipeline")
    vault_id: str = Field(..., description="ID of the vault containing the documents")
    documents: List[Dict[str, Any]] = Field(..., description="Documents in the batch")
    status: str = Field(..., description="Current batch status")
    priority: int = Field(..., description="Execution priority")
    # Execution statistics
    total_documents: int = Field(..., description="Total number of documents")
    successful_documents: int = Field(..., description="Number of successful documents")
    failed_documents: int = Field(..., description="Number of failed documents")
    pipeline_execution_id: str = Field(..., description="ID of the associated pipeline execution")
    # Timing information
    submitted_at: str = Field(..., description="Batch execution submission time in utc tz iso-format")
    started_at: str = Field(..., description="Batch execution start time in utc tz iso-format")
    completed_at: str = Field(..., description="Batch execution completion time in utc tz iso-format")
    # Additional metadata
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    source_batch_id: str = Field(..., description="ID of the source batch if applicable")


class DocumentResult(BaseModel):
    """Model for individual document processing results"""
    document_id: str = Field(..., description="Document ID")
    result: str = Field(..., description="Processing status (success/failed)")
    reason: Optional[str] = Field(None, description="Reason for the result status")
    elapsed_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    step_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from each step")
    data: Dict[str, Any] = Field(default_factory=dict, description="Document data")
    summary_data: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")


class PipelineExecutionResult(BaseModel):
    """Model for pipeline execution results"""
    id: str = Field(..., description="Unique id of the execution result")
    pipeline_name: str = Field(..., description="Name of the executed pipeline")
    result: str = Field(..., description="Overall execution result (Success/Failed)")
    reason: str = Field(..., description="Reason for the execution result")
    elapsed_time_secs: float = Field(..., description="Total pipeline execution time in seconds")
    batch_execution_id: str = Field(..., description="ID of the related batch execution")
    vault_id: str = Field(..., description="ID of the vault where documents are stored")
    # Document results
    document_results: List[DocumentResult] = Field(default_factory=list, description="Results for each document")
    # Summary statistics
    summary_stats: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
    
    
    # Timing information
    started_at: Optional[str] = Field(None, description="Execution start time in utc timezone in ISO format")
    completed_at: Optional[str] = Field(None, description="Execution completion time in utc timezone in ISO format")