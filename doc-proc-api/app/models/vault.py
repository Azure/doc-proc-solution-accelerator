from typing import Dict, List, Any, Optional, Generic, TypeVar
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.models.common import BaseDoc


T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number (1-based)")
    pageSize: int = Field(..., description="Number of items per page")
    totalPages: int = Field(..., description="Total number of pages")


class VaultStatus(str, Enum):
    """Enum for vault status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class DocumentProcessingConfig(BaseModel):
    """Configuration for document processing"""
    auto_process_documents: bool = Field(default=True, description="Automatically process documents upon addition")
    supported_formats: List[str] = Field(default=["pdf", "docx", "pptx", "excel"], description="Supported document formats")


class StorageConfig(BaseModel):
    """Storage configuration"""
    account_name: str = Field(..., description="Azure Storage account name")
    container_name: str = Field(..., description="Azure Blob container name")
    credential_type: str = Field(
        default="default_azure_credential", 
        description="Type of credential to use: 'default_azure_credential' or 'connection_string'"
    )
    connection_string: Optional[str] = Field(None, description="Storage connection string")


class ContentIdentifierInfo(BaseModel):
    canonical_id : str = Field(default=..., description='Canonical identifier for the content')
    unique_id : Optional[str] = Field(default=None, description='Unique identifier for the content')
    multipart_id : list[str] = Field(default_factory=list, description='List of multipart identifiers for the content')
    source_id : str = Field(default=..., description='Identifier for the source instance of the content')
    source_name : Optional[str] = Field(default=None, description='Name of the source instance of the content')
    metadata : dict[str, object] | None = Field(default=None, description='Metadata associated with the content')


class DocumentInfo(BaseModel):
    """Information about a document in a vault"""
    id: str = Field(..., description="Document ID")
    name: str = Field(..., description="Document name")
    vault_id: str = Field(..., description="ID of the vault this document belongs to")
    content_id: ContentIdentifierInfo = Field(..., description="Content identifier information")
    submit_date: str = Field(..., description="Submission date in ISO format")
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


class VaultCreateRequest(BaseModel):
    """Request model for creating a vault"""
    name: str = Field(..., description="Vault name")
    description: Optional[str] = Field(None, description="Vault description")
    pipeline_name: str = Field(..., description="Associated pipeline name")
    source_instance_name: Optional[str] = Field(None, description="Name of the associated source instance")
    processing_config: Optional[DocumentProcessingConfig] = Field(
        None, description="Processing configuration"
    )
    storage_config: Optional[StorageConfig] = Field(None, description="Storage configuration, uses default storage if not provided")
    

class VaultUpdateRequest(BaseModel):
    """Request model for updating a vault"""
    description: Optional[str] = Field(None, description="Vault description")
    processing_config: Optional[DocumentProcessingConfig] = Field(None, description="Processing configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
class Vault(BaseDoc):
    """Model for document vault"""
    status: VaultStatus = Field(default=VaultStatus.ACTIVE, description="Vault status")
    pipeline_name: str = Field(..., description="Associated pipeline name")
    source_instance_name: Optional[str] = Field(None, description="Name of the associated source instance")
    # Configuration
    processing_config: DocumentProcessingConfig = Field(default_factory=DocumentProcessingConfig, description="Document processing configuration")
    storage_config: StorageConfig = Field(default_factory=StorageConfig, description="Storage configuration")
    # Statistics
    stats: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Vault statistics")
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
