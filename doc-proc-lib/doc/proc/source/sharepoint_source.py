import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import fnmatch
import json

import httpx
from msal import ConfidentialClientApplication

from doc.proc.source.source_base import SourceBase, SourceItem, SourceItemMetadata
from doc.proc.models import ServiceExecutionError, ContentIdentifier

logger = logging.getLogger("doc.proc.source.sharepoint_source")


class SharePointSource(SourceBase):
    """SharePoint source for crawling and retrieving documents from SharePoint sites and document libraries."""

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.tenant_id = settings.get('tenant_id')
        self.client_id = settings.get('client_id')
        self.client_secret = settings.get('client_secret')
        self.site_url = settings.get('site_url')
        self.library_name = settings.get('library_name', 'Documents')
        
        # Validate required settings
        for key in ['tenant_id', 'client_id', 'client_secret', 'site_url']:
            value = settings.get(key)
            if not value:
                raise ValueError(f"Settings key '{key}' is required")
            
            # Read from environment variable if in ${ENV_VAR_NAME} format
            if value.startswith('${') and value.endswith('}'):
                env_var_name = value[2:-1]
                env_value = os.getenv(env_var_name)
                if not env_value:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
                setattr(self, key, env_value)
            else:
                setattr(self, key, value)

        # Parse the site URL to get tenant and site information
        self._parse_site_url()
        
        self._access_token = None
        self._token_expires_at = None
        self._http_client = None

    def _parse_site_url(self):
        """Parse SharePoint site URL to extract tenant and site path."""
        # Example: https://contoso.sharepoint.com/sites/projectsite
        # or: https://contoso.sharepoint.com/
        if not self.site_url.startswith('https://'):
            raise ValueError("Site URL must start with https://")
        
        parts = self.site_url.replace('https://', '').split('/')
        if len(parts) < 1 or not parts[0].endswith('.sharepoint.com'):
            raise ValueError("Invalid SharePoint site URL format")
        
        self.sharepoint_hostname = parts[0]
        self.site_path = '/' + '/'.join(parts[1:]) if len(parts) > 1 else '/'
        
        # Clean up site path
        if not self.site_path.endswith('/'):
            self.site_path += '/'

    async def _get_access_token(self) -> str:
        """Get or refresh the access token for SharePoint API."""
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        try:
            # Create MSAL client application
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )

            # Get token for SharePoint
            scopes = [f"https://{self.sharepoint_hostname}/.default"]
            result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" not in result:
                raise ServiceExecutionError(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")

            self._access_token = result["access_token"]
            # Set expiration time (typically 1 hour, but we'll refresh 5 minutes early)
            expires_in = result.get("expires_in", 3600) - 300  # 5 minutes buffer
            self._token_expires_at = datetime.now() + datetime.timedelta(seconds=expires_in)

            return self._access_token

        except Exception as e:
            logger.error(f"Failed to get SharePoint access token: {e}")
            raise ServiceExecutionError(f"Failed to get SharePoint access token: {e}")

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def _make_graph_request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make a request to Microsoft Graph API."""
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        try:
            http_client = self._get_http_client()
            
            if method.upper() == "GET":
                response = await http_client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await http_client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Graph API request failed: {e.response.status_code} - {e.response.text}")
            raise ServiceExecutionError(f"SharePoint API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Graph API request error: {e}")
            raise ServiceExecutionError(f"SharePoint API request error: {e}")

    async def test_connection(self) -> bool:
        """Test the connection to SharePoint."""
        try:
            # Try to get site information
            site_endpoint = f"/sites/{self.sharepoint_hostname.replace('.sharepoint.com', '')}:{self.site_path}"
            await self._make_graph_request(site_endpoint)
            logger.info(f"Successfully connected to SharePoint site: {self.site_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SharePoint: {e}")
            raise ServiceExecutionError(f"Failed to connect to SharePoint: {e}")

    def _matches_filter(self, file_name: str, file_filters: Optional[List[str]]) -> bool:
        """Check if file name matches any of the file filters."""
        if not file_filters:
            return True
        
        for pattern in file_filters:
            if fnmatch.fnmatch(file_name.lower(), pattern.lower()):
                return True
        
        return False

    def _create_content_identifier(self, file_path: str, item_id: str) -> ContentIdentifier:
        """Create a ContentIdentifier for a SharePoint file."""
        container_path = f"{self.site_path.strip('/')}/{self.library_name}"
        canonical_id = f"{self.type}://{self.sharepoint_hostname}{self.site_path}{self.library_name}/{file_path}"
        content_identifier = ContentIdentifier(
            canonical_id=canonical_id,
            unique_id=item_id,
            source_id=f"{self.type}_{self.name}",
            source_name=self.name,
            source_type=self.type,
            container=container_path,
            path=file_path
        )
        
        # Validate that all required fields are populated
        self._validate_content_identifier(content_identifier)
        return content_identifier

    def _create_source_item_metadata(self, drive_item: dict) -> SourceItemMetadata:
        """Create SourceItemMetadata from SharePoint drive item."""
        file_path = drive_item.get('webUrl', '').split('/')[-1] or drive_item['name']
        
        # Parse dates
        created_date = None
        modified_date = None
        
        if 'createdDateTime' in drive_item:
            created_date = datetime.fromisoformat(drive_item['createdDateTime'].replace('Z', '+00:00'))
        if 'lastModifiedDateTime' in drive_item:
            modified_date = datetime.fromisoformat(drive_item['lastModifiedDateTime'].replace('Z', '+00:00'))

        content_identifier = self._create_content_identifier(file_path, drive_item.get('id', ''))
        return SourceItemMetadata(
            content_identifier=content_identifier,
            name=drive_item['name'],
            size=drive_item.get('size', 0),
            modified_date=modified_date,
            created_date=created_date,
            content_type=drive_item.get('file', {}).get('mimeType'),
            etag=drive_item.get('eTag'),
            sharepoint_id=drive_item.get('id'),
            web_url=drive_item.get('webUrl'),
            created_by=drive_item.get('createdBy', {}).get('user', {}).get('displayName'),
            modified_by=drive_item.get('lastModifiedBy', {}).get('user', {}).get('displayName')
        )

    async def _get_drive_items(self, 
                              folder_path: str = "",
                              recursive: bool = True,
                              file_filters: Optional[List[str]] = None) -> AsyncGenerator[SourceItemMetadata, None]:
        """Get drive items from SharePoint document library."""
        try:
            # Get site information first
            site_endpoint = f"/sites/{self.sharepoint_hostname.replace('.sharepoint.com', '')}:{self.site_path}"
            site_info = await self._make_graph_request(site_endpoint)
            site_id = site_info['id']

            # Get drive (document library)
            drives_endpoint = f"/sites/{site_id}/drives"
            drives = await self._make_graph_request(drives_endpoint)
            
            drive_id = None
            for drive in drives.get('value', []):
                if drive['name'] == self.library_name:
                    drive_id = drive['id']
                    break
            
            if not drive_id:
                raise ServiceExecutionError(f"Document library '{self.library_name}' not found")

            # Get items from the drive
            if folder_path:
                items_endpoint = f"/drives/{drive_id}/root:/{folder_path}:/children"
            else:
                items_endpoint = f"/drives/{drive_id}/root/children"

            # Handle pagination
            while items_endpoint:
                response = await self._make_graph_request(items_endpoint)
                
                for item in response.get('value', []):
                    if 'folder' in item:
                        # It's a folder
                        if recursive:
                            folder_name = item['name']
                            new_folder_path = f"{folder_path}/{folder_name}".strip('/')
                            async for file_metadata in self._get_drive_items(
                                new_folder_path, recursive, file_filters
                            ):
                                yield file_metadata
                    elif 'file' in item:
                        # It's a file
                        if self._matches_filter(item['name'], file_filters):
                            metadata = self._create_source_item_metadata(item)
                            yield metadata

                # Check for next page
                items_endpoint = response.get('@odata.nextLink')
                if items_endpoint:
                    # Remove the base URL to get just the endpoint
                    items_endpoint = items_endpoint.replace('https://graph.microsoft.com/v1.0', '')

        except Exception as e:
            logger.error(f"Failed to get SharePoint drive items: {e}")
            raise ServiceExecutionError(f"Failed to get SharePoint drive items: {e}")

    async def crawl(self, 
                   path: Optional[str] = None,
                   recursive: bool = True,
                   crawl_depth: Optional[int] = None,
                   max_documents: Optional[int] = None,
                   file_filters: Optional[List[str]] = None,
                   incremental: Optional[bool] = True,
                   checkpoint_time: Optional[str] = None) -> AsyncGenerator[SourceItemMetadata, None]:
        """
        Crawl SharePoint to discover available files.
        
        Args:
            path: Starting folder path to crawl from (optional, defaults to root)
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
            start_path = path.strip('/') if path else ""
            async for metadata in self._get_drive_items(start_path, recursive, file_filters):
                yield metadata
                    
        except Exception as e:
            logger.error(f"Failed to crawl SharePoint: {e}")
            raise ServiceExecutionError(f"Failed to crawl SharePoint: {e}")

    async def retrieve_item(self, content_identifier: ContentIdentifier) -> SourceItem:
        """Retrieve a specific file from SharePoint including its content."""
        try:
            if not content_identifier.unique_id:
                raise ServiceExecutionError("SharePoint item ID is required for retrieval")

            # Download the file content
            download_endpoint = f"/drives/{content_identifier.container}/items/{content_identifier.unique_id}/content"
            
            token = await self._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            http_client = self._get_http_client()
            response = await http_client.get(
                f"https://graph.microsoft.com/v1.0{download_endpoint}",
                headers=headers
            )
            response.raise_for_status()
            content = response.content

            # Get file metadata
            metadata = await self.get_item_metadata(content_identifier)
            
            return SourceItem(
                content_identifier=content_identifier,
                metadata=metadata,
                content=content
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve SharePoint file '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to retrieve SharePoint file '{content_identifier.path}': {e}")

    async def get_item_metadata(self, content_identifier: ContentIdentifier) -> SourceItemMetadata:
        """Get metadata for a specific SharePoint file without downloading its content."""
        try:
            if not content_identifier.unique_id:
                raise ServiceExecutionError("SharePoint item ID is required for metadata retrieval")

            # Get item metadata
            item_endpoint = f"/drives/{content_identifier.container}/items/{content_identifier.unique_id}"
            item_data = await self._make_graph_request(item_endpoint)
            
            return self._create_source_item_metadata(item_data)
            
        except Exception as e:
            logger.error(f"Failed to get metadata for SharePoint file '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to get metadata for SharePoint file '{content_identifier.path}': {e}")

    async def item_exists(self, content_identifier: ContentIdentifier) -> bool:
        """Check if a file exists in SharePoint."""
        try:
            await self.get_item_metadata(content_identifier)
            return True
        except ServiceExecutionError:
            return False
        except Exception as e:
            logger.error(f"Failed to check existence of SharePoint file '{content_identifier.path}': {e}")
            raise ServiceExecutionError(f"Failed to check existence of SharePoint file '{content_identifier.path}': {e}")

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()