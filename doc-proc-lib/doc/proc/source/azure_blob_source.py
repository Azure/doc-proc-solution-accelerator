import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import fnmatch

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.storage.blob import BlobProperties
from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError

from doc.proc.providers.credential_provider import get_azure_credential
from doc.proc.source.source_base import SourceBase, SourceItem, SourceItemMetadata
from doc.proc.models import ServiceExecutionError, ContentIdentifier

logger = logging.getLogger("doc.proc.source.azure_blob_source")


class AzureBlobSource(SourceBase):
    """Azure Blob Storage source for crawling and retrieving documents from blob containers."""

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.storage_account_name = settings.get('account_name')
        self.container_name = settings.get('container_name')
        self.credential_type = settings.get('credential_type')
        self.credential_key = ''

        # Validate storage account name
        if not self.storage_account_name:
            raise ValueError("Settings key 'account_name' is required")

        # Read the storage account name from environment variable if in ${ENV_VAR_NAME} format
        if self.storage_account_name.startswith('${') and self.storage_account_name.endswith('}'):
            env_var_name = self.storage_account_name[2:-1]
            self.storage_account_name = os.getenv(env_var_name)
            if not self.storage_account_name:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")

        # Validate container name
        if not self.container_name:
            raise ValueError("Settings key 'container_name' is required")

        # Read the container name from environment variable if in ${ENV_VAR_NAME} format
        if self.container_name.startswith('${') and self.container_name.endswith('}'):
            env_var_name = self.container_name[2:-1]
            self.container_name = os.getenv(env_var_name)
            if not self.container_name:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        
        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        # Read the credential type from environment variable if in ${ENV_VAR_NAME} format
        if self.credential_type.startswith('${') and self.credential_type.endswith('}'):
            env_var_name = self.credential_type[2:-1]
            self.credential_type = os.getenv(env_var_name)
            if not self.credential_type:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        
        # Setup credentials based on type
        if self.credential_type == 'azure_key_credential':
            self.credential_key = settings.get('credential_key', '')
            if self.credential_key.startswith('${') and self.credential_key.endswith('}'):
                env_var_name = self.credential_key[2:-1]
                self.credential_key = os.getenv(env_var_name)
                if not self.credential_key:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            
            if not self.credential_key:
                raise ValueError("Settings key 'credential_key' is required when using 'azure_key_credential'")
        elif self.credential_type != 'default_azure_credential':
            raise ValueError(f"Unsupported credential type: {self.credential_type}")

        self._blob_service_client = None
        self._container_client = None

    def _get_blob_service_client(self) -> BlobServiceClient:
        """Get or create the blob service client."""
        if self._blob_service_client is None:
            account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
            
            if self.credential_type == 'azure_key_credential':
                
                # For key credential, use sync client first to get the key, then create async client
                self._blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.credential_key
                )
            else:  # default_azure_credential
                credential = get_azure_credential()
                self._blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential
                )
        
        return self._blob_service_client

    def _get_container_client(self) -> ContainerClient:
        """Get or create the container client."""
        if self._container_client is None:
            blob_service_client = self._get_blob_service_client()
            self._container_client = blob_service_client.get_container_client(self.container_name)
        
        return self._container_client

    async def test_connection(self) -> bool:
        """Test the connection to Azure Blob Storage."""
        try:
            container_client = self._get_container_client()
            # Try to get container properties to test connection
            await container_client.get_container_properties()
            logger.info(f"Successfully connected to Azure Blob Storage account '{self.storage_account_name}', container '{self.container_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Azure Blob Storage: {e}")
            raise ServiceExecutionError(f"Failed to connect to Azure Blob Storage: {e}")

    def _matches_filter(self, blob_name: str, file_filters: Optional[List[str]]) -> bool:
        """Check if blob name matches any of the file filters."""
        if not file_filters:
            return True
        
        for pattern in file_filters:
            if fnmatch.fnmatch(blob_name.lower(), pattern.lower()):
                return True
        
        return False

    def _create_content_identifier(self, blob_name: str) -> ContentIdentifier:
        """Create a ContentIdentifier for a blob."""
        canonical_id = f"{self.type}://{self.storage_account_name}/{self.container_name}/{blob_name}"
        content_identifier = ContentIdentifier(
            canonical_id=canonical_id,
            unique_id=self._generate_sha1_hash(canonical_id),
            source_id=f"{self.type}_{self.name}",
            source_name=self.name,
            source_type=self.type,
            container=self.container_name,
            path=blob_name,
            metadata={},
        )
        
        # Validate that all required fields are populated
        self._validate_content_identifier(content_identifier)
        return content_identifier

    def _create_source_item_metadata(self, blob_properties: BlobProperties) -> SourceItemMetadata:
        """Create SourceItemMetadata from blob properties."""
        content_identifier = self._create_content_identifier(blob_properties.name)
        return SourceItemMetadata(
            content_identifier=content_identifier,
            name=Path(blob_properties.name).name,
            size=blob_properties.size,
            modified_date=blob_properties.last_modified,
            created_date=blob_properties.creation_time,
            content_type=blob_properties.content_settings.content_type if blob_properties.content_settings else None,
            etag=blob_properties.etag,
            blob_type=str(blob_properties.blob_type) if blob_properties.blob_type else None,
            content_encoding=blob_properties.content_settings.content_encoding if blob_properties.content_settings else None,
            content_language=blob_properties.content_settings.content_language if blob_properties.content_settings else None,
            metadata=blob_properties.metadata or {}
        )

    async def crawl(self, 
                   path: Optional[str] = None,
                   recursive: bool = True,
                   crawl_depth: Optional[int] = None,
                   max_documents: Optional[int] = None,
                   file_filters: Optional[List[str]] = None,
                   incremental: Optional[bool] = True,
                   checkpoint_time: Optional[datetime] = None) -> AsyncGenerator[SourceItemMetadata, None]:
        """
        Crawl Azure Blob Storage to discover available blobs.
        
        Args:
            path: Starting path prefix to crawl from (optional, defaults to root)
            recursive: Whether to crawl subdirectories recursively (always True for blob storage)
            crawl_depth: Maximum depth to crawl (optional, defaults to unlimited)
            max_documents: Maximum number of documents to retrieve (optional, defaults to unlimited)
            file_filters: List of file patterns to filter by (e.g., ['*.pdf', '*.docx'])
            incremental: Whether to perform incremental crawling (not implemented)
            checkpoint_time: Last checkpoint time for incremental crawling (not implemented)

        Yields:
            SourceItemMetadata: Metadata for each discovered blob
        """
        try:
            container_client = self._get_container_client()
            
            logger.debug(f"Starting crawl in container '{self.container_name}' with path prefix '{path}', filters: {file_filters}' and checkpoint_time: {checkpoint_time}")
          
            # Create the prefix for blob listing
            name_starts_with = path.rstrip('/') + '/' if path else None
            
            # List all blobs with the given prefix and that are created/modified after checkpoint_time if provided
            async for blob in container_client.list_blobs(name_starts_with=name_starts_with):
                # Skip directories (blobs ending with /)
                if blob.name.endswith('/'):
                    continue
                
                if blob.last_modified and checkpoint_time:
                    if blob.last_modified <= checkpoint_time:
                        continue
                
                # Apply file filters
                if self._matches_filter(blob.name, file_filters):
                    metadata = self._create_source_item_metadata(blob)
                    yield metadata
                    
        except Exception as e:
            logger.error(f"Failed to crawl Azure Blob Storage: {e}")
            raise ServiceExecutionError(f"Failed to crawl Azure Blob Storage: {e}")

    async def retrieve_item(self, content_identifier: ContentIdentifier) -> SourceItem:
        """Retrieve a specific blob from Azure Blob Storage including its content."""
        try:
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(content_identifier.path)
            
            # Download blob content
            blob_data = await blob_client.download_blob()
            content = await blob_data.readall()
            
            # Get blob properties for metadata
            properties = await blob_client.get_blob_properties()
            metadata = self._create_source_item_metadata(properties)
            
            return SourceItem(
                content_identifier=content_identifier,
                metadata=metadata,
                content=content
            )
            
        except ResourceNotFoundError:
            raise ServiceExecutionError(f"Blob not found: {content_identifier.path}")
        except Exception as e:
            logger.error(f"Failed to retrieve blob '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to retrieve blob '{content_identifier.path}': {e}")

    async def get_item_metadata(self, content_identifier: ContentIdentifier) -> SourceItemMetadata:
        """Get metadata for a specific blob without downloading its content."""
        try:
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(content_identifier.path)
            
            # Get blob properties
            properties = await blob_client.get_blob_properties()
            return self._create_source_item_metadata(properties)
            
        except ResourceNotFoundError:
            raise ServiceExecutionError(f"Blob not found: {content_identifier.path}")
        except Exception as e:
            logger.error(f"Failed to get metadata for blob '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to get metadata for blob '{content_identifier.path}': {e}")

    async def item_exists(self, content_identifier: ContentIdentifier) -> bool:
        """Check if a blob exists in Azure Blob Storage."""
        try:
            container_client = self._get_container_client()
            blob_client = container_client.get_blob_client(content_identifier.path)
            
            # Check if blob exists
            return await blob_client.exists()
            
        except Exception as e:
            logger.error(f"Failed to check existence of blob '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to check existence of blob '{content_identifier.path}': {e}")

    async def close(self):
        """Close the blob service client."""
        if self._blob_service_client:
            await self._blob_service_client.close()
            self._blob_service_client = None
            self._container_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()