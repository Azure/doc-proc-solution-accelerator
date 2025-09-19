from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.models.common import BaseDoc


class VaultStatus(str, Enum):
    """Enum for vault status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class DocumentProcessingConfig(BaseModel):
    """Configuration for document processing"""
    auto_process_documents: bool = Field(
        default=True, description="Automatically process documents upon addition"
    )
    supported_formats: List[str] = Field(
        default=["pdf", "docx", "pptx", "excel"], 
        description="Supported document formats"
    )


class StorageConfig(BaseModel):
    """Storage configuration"""
    account_name: str = Field(..., description="Azure Storage account name")
    container_name: str = Field(..., description="Azure Blob container name")
    credential_type: str = Field(
        default="default_azure_credential", 
        description="Type of credential to use: 'default_azure_credential' or 'connection_string'"
    )
    connection_string: Optional[str] = Field(None, description="Storage connection string")


class DocumentInfo(BaseModel):
    """Information about a document in a vault"""
    id: str = Field(..., description="Document ID")
    name: str = Field(..., description="Document name")
    vault_id: str = Field(..., description="ID of the vault this document belongs to")
    size_bytes: int = Field(..., description="Document size in bytes")
    content_type: str = Field(..., description="Document content type")
    blob_url: str = Field(..., description="URL to the document in blob storage")
    blob_details: Optional[Dict[str, str]] = Field(None, description="Details about the blob (storage_account, container, blob_name)")
    upload_date: str = Field(..., description="Upload date in ISO format")
    processed_date: Optional[str] = Field(None, description="Processing date in ISO format")
    status: str = Field(default="pending", description="Processing status")
    source: Optional[str] = Field(None, description="Source of the document, where the document originated from. E.g., 'user_upload', 'api_upload', 'crawler', etc.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UploadDocumentResponse(BaseModel):
    """Response model for uploading documents"""
    filename: str = Field(..., description="Name of the uploaded file")
    document: Optional[DocumentInfo] = Field(None, description="Information about the uploaded document")
    error: Optional[str] = Field(None, description="Status message")


class AddDocumentRequest(BaseModel):
    """Request model for adding a document to a vault"""
    name: str = Field(..., description="Document name")
    blob_url: str = Field(..., description="URL to the document in blob storage")
    source: Optional[str] = Field(None, description="Source of the document, where the document originated from. E.g., 'user_upload', 'api_upload', 'crawler', etc.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VaultStats(BaseModel):
    """Statistics for a vault"""
    total_documents: int = Field(default=0, description="Total number of documents")
    processed_documents: int = Field(default=0, description="Number of processed documents")
    pending_documents: int = Field(default=0, description="Number of pending documents")
    failed_documents: int = Field(default=0, description="Number of failed documents")
    total_size_bytes: int = Field(default=0, description="Total size in bytes")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class VaultCreateRequest(BaseModel):
    """Request model for creating a vault"""
    name: str = Field(..., description="Vault name")
    description: Optional[str] = Field(None, description="Vault description")
    pipeline_name: str = Field(..., description="Associated pipeline name")
    processing_config: Optional[DocumentProcessingConfig] = Field(
        None, description="Processing configuration"
    )
    storage_config: Optional[StorageConfig] = Field(None, description="Storage configuration, uses default storage if not provided")


class VaultUpdateRequest(BaseModel):
    """Request model for updating a vault"""
    id: str = Field(..., description="Vault ID")
    description: Optional[str] = Field(None, description="Vault description")
    status: Optional[VaultStatus] = Field(None, description="Vault status")
    pipeline_name: Optional[str] = Field(None, description="Associated pipeline name")
    processing_config: Optional[DocumentProcessingConfig] = Field(
        None, description="Processing configuration"
    )
    

class Vault(BaseDoc):
    """Model for document vault"""
    status: VaultStatus = Field(default=VaultStatus.ACTIVE, description="Vault status")
    pipeline_name: str = Field(..., description="Associated pipeline name")
    
    # Configuration
    processing_config: DocumentProcessingConfig = Field(
        default_factory=DocumentProcessingConfig,
        description="Document processing configuration"
    )
    storage_config: StorageConfig = Field(
        default_factory=StorageConfig, description="Storage configuration"
    )
    # Statistics
    stats: VaultStats = Field(
        default_factory=VaultStats,
        description="Vault statistics"
    )
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VaultProcessingRequest(BaseModel):
    """Request to start processing documents in a vault"""
    vault_id: str = Field(..., description="Vault ID")
    document_ids: Optional[List[str]] = Field(
        None, description="Specific document IDs to process (if None, process all)"
    )
    force_reprocess: bool = Field(
        default=False, description="Force reprocessing of already processed documents"
    )


class VaultAuditLog(BaseModel):
    """Audit log entry for vault operations"""
    timestamp: str = Field(..., description="Timestamp of the log entry in ISO format")
    operation: str = Field(..., description="Operation performed (e.g., 'add_document', 'process_documents')")
    user: Optional[str] = Field(None, description="User who performed the operation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details about the operation")