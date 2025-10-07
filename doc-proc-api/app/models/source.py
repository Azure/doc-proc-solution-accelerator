from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from app.models.common import BaseDoc

class SourceSettingsSchema(BaseModel):
    """Schema definition for individual source setting parameters"""
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    pattern: Optional[str] = None
    env_var: Optional[str] = None
    default: Optional[str | int | float | bool] = None
    minimum: Optional[int | float] = None
    maximum: Optional[int | float] = None
    enum: Optional[List[str]] = None
    sensitive: Optional[bool] = None


class SourceUIMetadata(BaseModel):
    """UI metadata for source display"""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class SourceCatalogDefinition(BaseModel):
    """Source catalog definition from YAML"""
    id: str
    name: str
    description: str
    type: str
    module_name: str
    module_path: str
    class_name: str
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    settings_schema: Optional[Dict[str, SourceSettingsSchema]] = None
    ui_metadata: Optional[SourceUIMetadata] = None


class SourceStatus(BaseModel):
    """Source connection status information"""
    status: str = Field(..., description="Status: 'connected', 'error', 'testing', 'unknown'")
    message: Optional[str] = Field(None, description="Status message or error details")
    tested_at: Optional[str] = Field(None, description="Timestamp when connection was last tested. In UTC tz ISO 8601 format")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")


class SourceTestConnectionResponse(BaseModel):
    """Response from source connection test"""
    instance_id: str
    instance_name: Optional[str] = None
    source_type: Optional[str] = None
    status: str = Field(..., description="Connection test result: 'connected', 'error', 'testing'")
    message: str = Field(..., description="Connection test message")
    tested_at: str = Field(..., description="Timestamp when test was performed. In UTC tz ISO 8601 format")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional test details")


class SourceInstanceCrawlerSettings(BaseModel):
    """Crawler-specific settings for a source instance"""
    crawl_interval_minutes: Optional[int] = Field(60, description="Interval in minutes between crawls")
    max_documents: Optional[int] = Field(100, description="Maximum number of documents to crawl per run")
    processing_batch_size: Optional[int] = Field(10, description="Number of documents in a batch to submit for processing")
    file_filters: Optional[List[str]] = Field(default_factory=list, description="List of file patterns to include/exclude")
    incremental: Optional[bool] = Field(True, description="Whether to perform incremental crawling")
    crawl_depth: Optional[int] = Field(3, description="Depth of crawling (for web sources)")
    check_for_updates: Optional[bool] = Field(False, description="Whether to check for updates in previously crawled documents")
    checkpoint_time: Optional[str] = Field(None, description="Last checkpoint time for incremental crawling. In UTC tz ISO 8601 format")
    pause_on_error: Optional[bool] = Field(False, description="Whether to pause crawling on errors instead of retrying")
    skip_failed_documents: Optional[bool] = Field(True, description="Whether to skip documents that fail reterieval")
    additional_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional crawler-specific settings")


class SourceInstance(BaseModel):
    """Source instance configuration"""
    id: str = Field(..., description="Unique id, used as partition key")
    name: str = Field(..., description="Name of the source instance")
    source_catalog_id: str = Field(..., description="ID of the source in the source catalog")
    description: Optional[str] = Field(None, description="Description of the source instance")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Source-specific settings")
    crawler_settings: Optional[SourceInstanceCrawlerSettings] = Field(default_factory=SourceInstanceCrawlerSettings, description="Crawler-specific settings")
    enabled: bool = Field(True, description="Whether the source instance is enabled")
    test_connection: bool = Field(True, description="Whether to test connection on initialization")
    status: Optional[SourceStatus] = Field(None, description="Current connection status")
    catalog_definition: Optional[SourceCatalogDefinition] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SourceInstanceCreateRequest(BaseModel):
    """Request to create a new source instance"""
    name: str = Field(..., description="Name of the source instance")
    source_catalog_id: str = Field(..., description="ID of the source in the source catalog")
    description: Optional[str] = Field(None, description="Description of the source instance")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Source-specific settings")
    crawler_settings: Optional[SourceInstanceCrawlerSettings] = Field(default_factory=SourceInstanceCrawlerSettings, description="Crawler-specific settings")
    enabled: bool = Field(True, description="Whether the source instance is enabled")
    test_connection: bool = Field(True, description="Whether to test connection on initialization")


class SourceInstanceUpdateRequest(BaseModel):
    """Request to update an existing source instance"""
    name: str = Field(..., description="Name of the source instance")
    source_catalog_id: Optional[str] = Field(None, description="ID of the source in the source catalog")
    description: Optional[str] = Field(None, description="Description of the source instance")
    settings: Optional[Dict[str, Any]] = Field(None, description="Source-specific settings")
    crawler_settings: Optional[SourceInstanceCrawlerSettings] = Field(default_factory=SourceInstanceCrawlerSettings, description="Crawler-specific settings")
    enabled: Optional[bool] = Field(None, description="Whether the source instance is enabled")
    test_connection: Optional[bool] = Field(None, description="Whether to test connection on initialization")