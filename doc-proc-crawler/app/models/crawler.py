from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class CrawlStatus(str, Enum):
    """Status of a crawl execution"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class CrawlTriggerType(str, Enum):
    """Type of trigger that initiated the crawl"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    AUTO = "auto"
    RETRY = "retry"


# Define SourceInstance compatible with doc-proc-api model structure
class SourceInstance(BaseModel):
    """Source instance model compatible with doc-proc-api"""
    id: str
    name: str
    source_catalog_id: str  # References source catalog
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    crawler_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enabled: bool = True
    test_connection: bool = True
    status: Optional[Dict[str, Any]] = None  # Connection status
    catalog_definition: Optional[Dict[str, Any]] = None
    is_system: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Runtime crawl state
    last_crawl_at: Optional[str] = None
    last_crawl_status: Optional[CrawlStatus] = None
    crawl_checkpoint: Optional[str] = None


class CrawlExecution(BaseModel):
    """Model representing a crawl execution record"""
    id: str
    source_instance_id: str
    vault_id: str
    
    # Execution details
    status: CrawlStatus = CrawlStatus.PENDING
    trigger_type: CrawlTriggerType = CrawlTriggerType.MANUAL
    worker_id: Optional[str] = None
    
    # Timing
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    # Progress tracking
    total_files_found: Optional[int] = None
    files_processed: int = 0
    files_uploaded: int = 0
    files_queued: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Results
    documents_queued: List[dict] = Field(default_factory=list)  # Document metadata
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CrawlerWorkerStats(BaseModel):
    """Statistics for a crawler worker instance"""
    worker_id: str
    started_at: datetime
    last_activity_at: datetime
    
    # Current state
    current_source_instance_id: Optional[str] = None
    current_crawl_execution_id: Optional[str] = None
    processing_since: Optional[datetime] = None
    
    # Counters
    total_crawls_processed: int = 0
    total_documents_queued: int = 0
    total_files_processed: int = 0
    total_errors: int = 0
    
    # Performance metrics
    average_crawl_duration_seconds: Optional[float] = None
    documents_per_minute: Optional[float] = None


# Use SourceItemMetadata from doc-proc-lib instead of DocumentMetadata
# This will be imported in the crawler_worker from doc.proc.source.source_base


class CrawlResult(BaseModel):
    """Result of crawling a single document/file"""
    success: bool
    file_path: str
    document_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Will contain SourceItemMetadata dict
    processing_time_seconds: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }