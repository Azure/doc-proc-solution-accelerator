import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import fnmatch

from azure.identity.aio import DefaultAzureCredential
from azure.storage.fileshare.aio import ShareServiceClient, ShareClient, ShareFileClient
from azure.storage.fileshare import FileProperties, DirectoryProperties
from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError

from doc.proc.source.source_base import SourceBase, SourceItem, SourceItemMetadata
from doc.proc.models import ServiceExecutionError, ContentIdentifier

logger = logging.getLogger("doc.proc.source.azure_files_source")


class AzureFilesSource(SourceBase):
    """Azure Files source for crawling and retrieving documents from file shares."""

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.storage_account_name = settings.get('account_name')
        self.share_name = settings.get('share_name')
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

        # Validate share name
        if not self.share_name:
            raise ValueError("Settings key 'share_name' is required")

        # Read the share name from environment variable if in ${ENV_VAR_NAME} format
        if self.share_name.startswith('${') and self.share_name.endswith('}'):
            env_var_name = self.share_name[2:-1]
            self.share_name = os.getenv(env_var_name)
            if not self.share_name:
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

        self._share_service_client = None
        self._share_client = None

    def _get_share_service_client(self) -> ShareServiceClient:
        """Get or create the share service client."""
        if self._share_service_client is None:
            account_url = f"https://{self.storage_account_name}.file.core.windows.net"
            
            if self.credential_type == 'azure_key_credential':
                from azure.storage.fileshare import ShareServiceClient
                # For key credential, use sync client first to get the key, then create async client
                self._share_service_client = ShareServiceClient(
                    account_url=account_url,
                    credential=self.credential_key
                )
            else:  # default_azure_credential
                credential = DefaultAzureCredential()
                self._share_service_client = ShareServiceClient(
                    account_url=account_url,
                    credential=credential
                )
        
        return self._share_service_client

    def _get_share_client(self) -> ShareClient:
        """Get or create the share client."""
        if self._share_client is None:
            share_service_client = self._get_share_service_client()
            self._share_client = share_service_client.get_share_client(self.share_name)
        
        return self._share_client

    async def test_connection(self) -> bool:
        """Test the connection to Azure Files."""
        try:
            share_client = self._get_share_client()
            # Try to get share properties to test connection
            await share_client.get_share_properties()
            logger.info(f"Successfully connected to Azure Files account '{self.storage_account_name}', share '{self.share_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Azure Files: {e}")
            raise ServiceExecutionError(f"Failed to connect to Azure Files: {e}")

    def _matches_filter(self, file_name: str, file_filters: Optional[List[str]]) -> bool:
        """Check if file name matches any of the file filters."""
        if not file_filters:
            return True
        
        for pattern in file_filters:
            if fnmatch.fnmatch(file_name.lower(), pattern.lower()):
                return True
        
        return False

    def _create_content_identifier(self, file_path: str) -> ContentIdentifier:
        """Create a ContentIdentifier for a file."""
        canonical_id = f"{self.type}://{self.storage_account_name}/{self.share_name}/{file_path}"
        content_identifier = ContentIdentifier(
            canonical_id=canonical_id,
            source_id=f"{self.type}_{self.name}",
            source_name=self.name,
            source_type=self.type,
            container=self.share_name,
            path=file_path
        )
        
        # Validate that all required fields are populated
        self._validate_content_identifier(content_identifier)
        return content_identifier

    def _create_source_item_metadata(self, file_properties: FileProperties, file_path: str) -> SourceItemMetadata:
        """Create SourceItemMetadata from file properties."""
        content_identifier = self._create_content_identifier(file_path)
        return SourceItemMetadata(
            content_identifier=content_identifier,
            name=Path(file_path).name,
            size=file_properties.size,
            modified_date=file_properties.last_modified,
            created_date=file_properties.creation_time,
            content_type=file_properties.content_settings.content_type if file_properties.content_settings else None,
            etag=file_properties.etag,
            content_encoding=file_properties.content_settings.content_encoding if file_properties.content_settings else None,
            content_language=file_properties.content_settings.content_language if file_properties.content_settings else None,
            metadata=file_properties.metadata or {}
        )

    async def _crawl_directory(self, 
                              share_client: ShareClient,
                              directory_path: str = "",
                              recursive: bool = True,
                              file_filters: Optional[List[str]] = None) -> AsyncGenerator[SourceItemMetadata, None]:
        """Recursively crawl a directory in the file share."""
        try:
            # List all items in the directory
            async for item in share_client.list_directories_and_files(directory_name=directory_path):
                item_path = f"{directory_path}/{item['name']}".lstrip('/')
                
                if item['is_directory']:
                    # If it's a directory and we're doing recursive crawling, crawl into it
                    if recursive:
                        async for file_metadata in self._crawl_directory(
                            share_client, item_path, recursive, file_filters
                        ):
                            yield file_metadata
                else:
                    # It's a file, apply filters and yield metadata
                    if self._matches_filter(item['name'], file_filters):
                        # Get file properties
                        file_client = share_client.get_file_client(item_path)
                        file_properties = await file_client.get_file_properties()
                        metadata = self._create_source_item_metadata(file_properties, item_path)
                        yield metadata
                        
        except Exception as e:
            logger.error(f"Failed to crawl directory '{directory_path}': {e}")
            raise ServiceExecutionError(f"Failed to crawl directory '{directory_path}': {e}")

    async def crawl(self, 
                   path: Optional[str] = None,
                   recursive: bool = True,
                   crawl_depth: Optional[int] = None,
                   max_documents: Optional[int] = None,
                   file_filters: Optional[List[str]] = None,
                   incremental: Optional[bool] = True,
                   checkpoint_time: Optional[str] = None) -> AsyncGenerator[SourceItemMetadata, None]:
        """
        Crawl Azure Files to discover available files.
        
        Args:
            path: Starting directory path to crawl from (optional, defaults to root)
            recursive: Whether to crawl subdirectories recursively
            crawl_depth: Maximum depth to crawl (optional, defaults to unlimited)
            max_documents: Maximum number of documents to retrieve (optional, defaults to unlimited)
            file_filters: List of file patterns to filter by (e.g., ['*.pdf', '*.docx'])
            incremental: Whether to perform incremental crawling (not implemented)
            checkpoint_time: Last checkpoint time for incremental crawling (not implemented)

        Yields:
            SourceItemMetadata: Metadata for each discovered file
        """
        try:
            share_client = self._get_share_client()
            
            # Start crawling from the specified path or root
            start_path = path.strip('/') if path else ""
            
            async for metadata in self._crawl_directory(share_client, start_path, recursive, file_filters):
                yield metadata
                    
        except Exception as e:
            logger.error(f"Failed to crawl Azure Files: {e}")
            raise ServiceExecutionError(f"Failed to crawl Azure Files: {e}")

    async def retrieve_item(self, content_identifier: ContentIdentifier) -> SourceItem:
        """Retrieve a specific file from Azure Files including its content."""
        try:
            share_client = self._get_share_client()
            file_client = share_client.get_file_client(content_identifier.path)
            
            # Download file content
            file_data = await file_client.download_file()
            content = await file_data.readall()
            
            # Get file properties for metadata
            properties = await file_client.get_file_properties()
            metadata = self._create_source_item_metadata(properties, content_identifier.path)
            
            return SourceItem(
                content_identifier=content_identifier,
                metadata=metadata,
                content=content
            )
            
        except ResourceNotFoundError:
            raise ServiceExecutionError(f"File not found: {content_identifier.path}")
        except Exception as e:
            logger.error(f"Failed to retrieve file '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to retrieve file '{content_identifier.path}': {e}")

    async def get_item_metadata(self, content_identifier: ContentIdentifier) -> SourceItemMetadata:
        """Get metadata for a specific file without downloading its content."""
        try:
            share_client = self._get_share_client()
            file_client = share_client.get_file_client(content_identifier.path)
            
            # Get file properties
            properties = await file_client.get_file_properties()
            return self._create_source_item_metadata(properties, content_identifier.path)
            
        except ResourceNotFoundError:
            raise ServiceExecutionError(f"File not found: {content_identifier.path}")
        except Exception as e:
            logger.error(f"Failed to get metadata for file '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to get metadata for file '{content_identifier.path}': {e}")

    async def item_exists(self, content_identifier: ContentIdentifier) -> bool:
        """Check if a file exists in Azure Files."""
        try:
            share_client = self._get_share_client()
            file_client = share_client.get_file_client(content_identifier.path)
            
            # Check if file exists
            return await file_client.exists()
            
        except Exception as e:
            logger.error(f"Failed to check existence of file '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to check existence of file '{content_identifier.path}': {e}")

    async def close(self):
        """Close the share service client."""
        if self._share_service_client:
            await self._share_service_client.close()
            self._share_service_client = None
            self._share_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()