from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from .common import BaseDoc


class VaultStatus(str, Enum):
    """Enum for vault status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
    ERROR = "error"


class DocumentProcessingConfig(BaseModel):
    """Configuration for document processing"""
    chunk_size: int = Field(default=512, description="Size of text chunks")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    enable_ocr: bool = Field(default=False, description="Enable OCR for images")
    supported_formats: List[str] = Field(
        default=["pdf", "docx", "txt", "md"], 
        description="Supported document formats"
    )


class AzureSearchConfig(BaseModel):
    """Azure Search configuration"""
    endpoint: str = Field(..., description="Azure Search endpoint")
    index_name: str = Field(..., description="Search index name")
    api_version: str = Field(default="2023-11-01", description="API version")


class StorageConfig(BaseModel):
    """Storage configuration"""
    container_name: str = Field(..., description="Azure Blob container name")
    connection_string: Optional[str] = Field(None, description="Storage connection string")


class DocumentInfo(BaseModel):
    """Information about a document in a vault"""
    id: str = Field(..., description="Document ID")
    name: str = Field(..., description="Document name")
    size_bytes: int = Field(..., description="Document size in bytes")
    content_type: str = Field(..., description="Document content type")
    upload_date: str = Field(..., description="Upload date in ISO format")
    processed_date: Optional[str] = Field(None, description="Processing date in ISO format")
    status: str = Field(default="pending", description="Processing status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VaultStats(BaseModel):
    """Statistics for a vault"""
    total_documents: int = Field(default=0, description="Total number of documents")
    processed_documents: int = Field(default=0, description="Number of processed documents")
    pending_documents: int = Field(default=0, description="Number of pending documents")
    failed_documents: int = Field(default=0, description="Number of failed documents")
    total_size_bytes: int = Field(default=0, description="Total size in bytes")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class Vault(BaseDoc):
    """Model for document vault"""
    status: VaultStatus = Field(default=VaultStatus.ACTIVE, description="Vault status")
    pipeline_id: Optional[str] = Field(None, description="Associated pipeline ID")
    
    # Configuration
    processing_config: DocumentProcessingConfig = Field(
        default_factory=DocumentProcessingConfig,
        description="Document processing configuration"
    )
    azure_search_config: Optional[AzureSearchConfig] = Field(
        None, description="Azure Search configuration"
    )
    storage_config: Optional[StorageConfig] = Field(
        None, description="Storage configuration"
    )
    
    # Statistics
    stats: VaultStats = Field(
        default_factory=VaultStats,
        description="Vault statistics"
    )
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VaultCreateRequest(BaseModel):
    """Request model for creating a vault"""
    name: str = Field(..., description="Vault name")
    description: Optional[str] = Field(None, description="Vault description")
    pipeline_id: Optional[str] = Field(None, description="Associated pipeline ID")
    processing_config: Optional[DocumentProcessingConfig] = Field(
        None, description="Processing configuration"
    )
    azure_search_config: Optional[AzureSearchConfig] = Field(
        None, description="Azure Search configuration"
    )
    storage_config: Optional[StorageConfig] = Field(
        None, description="Storage configuration"
    )


class VaultUpdateRequest(BaseModel):
    """Request model for updating a vault"""
    name: Optional[str] = Field(None, description="Vault name")
    description: Optional[str] = Field(None, description="Vault description")
    status: Optional[VaultStatus] = Field(None, description="Vault status")
    pipeline_id: Optional[str] = Field(None, description="Associated pipeline ID")
    processing_config: Optional[DocumentProcessingConfig] = Field(
        None, description="Processing configuration"
    )
    azure_search_config: Optional[AzureSearchConfig] = Field(
        None, description="Azure Search configuration"
    )
    storage_config: Optional[StorageConfig] = Field(
        None, description="Storage configuration"
    )


class VaultProcessingRequest(BaseModel):
    """Request to start processing documents in a vault"""
    vault_id: str = Field(..., description="Vault ID")
    document_ids: Optional[List[str]] = Field(
        None, description="Specific document IDs to process (if None, process all)"
    )
    force_reprocess: bool = Field(
        default=False, description="Force reprocessing of already processed documents"
    )
