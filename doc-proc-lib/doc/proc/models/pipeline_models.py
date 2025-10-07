from typing import List, Literal, Optional, Any, Dict
from pydantic import BaseModel

from doc.proc.models import ContentIdentifier, Document

class StepExecutionResult(BaseModel):
    """Model for the result of a step execution."""
    step_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "Skipped"] = "NotStarted"
    reason: Optional[str] = None  # Reason for skipping or failure, if applicable
    elapsed_time_secs: float
    error: Optional[str] = None  # Error message if the step fails
    error_message: Optional[str] = None  # Detailed error message if available
    error_traceback: Optional[str] = None  # Traceback of the error if available


class DocumentResult(BaseModel):
    """Model for the result of processing a single document."""
    document_id: ContentIdentifier
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None  # Reason for failure or partial success, if applicable
    elapsed_time_secs: float
    data: Dict[str, Any] = {}  # Final data output from document processing
    summary_data: Dict[str, Any] = {}  # Summary data for document processing
    step_results: List[StepExecutionResult] = []  # List of StepExecutionResult for each step
    

class PipelineExecutionResult(BaseModel):
    """Model for the output of a pipeline execution."""
    pipeline_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None  # Reason for failure or partial success, if applicable
    elapsed_time_secs: float
    document_results: List[DocumentResult] = []  # List of DocumentResult for each document processed
    summary_stats: dict = {}  # Summary statistics for the pipeline execution
    started_at: Optional[str] = None  # Start time in utc timezone in ISO format
    completed_at: Optional[str] = None  # Completion time in utc timezone in ISO format


class PipelineInput(BaseModel):
    """Model for the input data to a pipeline."""
    documents: List[Document] = []  # List of documents to be processed
    metadata: Optional[Dict[str, Any]] = None  # Optional metadata for the pipeline execution