import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient, ContainerClient

from doc.proc.service.service_base import ServiceBase, ServiceExecutionError

logger = logging.getLogger("doc.proc.service.blob_service") # need to specify the logger name as this module is loaded dynamically


class BlobService(ServiceBase):
    """Azure Blob Storage service for managing blob storage operations."""

    def __init__(self, name: str, type: str, settings:dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.storage_account_name = settings.get('account_name')
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
        
        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        # Read the credential type from environment variable if in ${ENV_VAR_NAME} format
        if self.credential_type.startswith('${') and self.credential_type.endswith('}'):
            env_var_name = self.credential_type[2:-1]
            self.credential_type = os.getenv(env_var_name)
            if not self.credential_type:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        
        # Validate credential key based on credential type
        if self.credential_type == 'azure_key_credential':
            self.credential_key = settings.get('credential_key')

            if not self.credential_key:
                raise ValueError("Settings key 'credential_key' is required for azure_key_credential")
            
            # Read the credential key from environment variable if in ${ENV_VAR_NAME} format
            if self.credential_key.startswith('${') and self.credential_key.endswith('}'):
                env_var_name = self.credential_key[2:-1]
                self.credential_key = os.getenv(env_var_name)
                if not self.credential_key:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            

        elif self.credential_type == 'default_azure_credential':
            self.credential_key = ''
        
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}. Supported types are 'azure_key_credential' and 'default_azure_credential'.")
        
        # Initialize service client and credential as None - will be set in initialize()
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.credential: Optional[DefaultAzureCredential] = None
        self._is_initialized: bool = False
        self._initialization_lock = asyncio.Lock()
        self._file_locks = {}  # Dictionary to store file-specific locks
        self._file_locks_lock = asyncio.Lock()  # Lock to protect the file locks dictionary
        self._active_operations = 0  # Track active operations
        self._operations_lock = asyncio.Lock()  # Lock to protect operation count


    async def initialize(self):
        """Initialize the BlobServiceClient and credentials if not already initialized."""
        async with self._initialization_lock:
            if self._is_initialized:
                return

            account_url = f"https://{self.storage_account_name}.blob.core.windows.net"

            logger.debug(f"Creating BlobServiceClient with account URL: {account_url} and credential type: {self.credential_type}")

            try:
                if self.credential_type == 'azure_key_credential' and self.credential_key:
                    # Use the account key directly
                    self.blob_service_client = BlobServiceClient(account_url=account_url, credential=self.credential_key)
                    logger.debug("Initialized BlobServiceClient with account key")
                
                elif self.credential_type == 'default_azure_credential':
                    # Create and store the credential for reuse
                    self.credential = DefaultAzureCredential()
                    self.blob_service_client = BlobServiceClient(account_url=account_url, credential=self.credential)
                    logger.debug("Initialized BlobServiceClient with DefaultAzureCredential")
                
                else:
                    raise ValueError(f"Invalid credential configuration: type={self.credential_type}, key_provided={bool(self.credential_key)}")

                self._is_initialized = True
                logger.debug("BlobServiceClient initialization completed successfully")

            except Exception as e:
                logger.error(f"Failed to initialize BlobServiceClient: {str(e)}")
                await self._cleanup()
                raise ServiceExecutionError(f"Failed to initialize Azure Blob Storage client: {str(e)}")

    async def __aenter__(self):
        """Enter the async context manager - increment operation count and ensure initialization."""
        await self.initialize()
        
        async with self._operations_lock:
            self._active_operations += 1
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager - decrement operation count but don't cleanup until explicitly closed."""
        async with self._operations_lock:
            self._active_operations -= 1
            if self._active_operations == 0:
                await self._cleanup()

    async def close(self):
        """Explicitly close the service and cleanup resources when no operations are active."""
        async with self._operations_lock:
            if self._active_operations > 0:
                logger.warning(f"Cannot close BlobService while {self._active_operations} operations are active")
                return
        
        await self._cleanup()

    async def _cleanup(self):
        """Clean up all async resources."""
        async with self._initialization_lock:
            if self.blob_service_client:
                try:
                    await self.blob_service_client.close()
                    logger.debug("BlobServiceClient closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing BlobServiceClient: {str(e)}")
                finally:
                    self.blob_service_client = None

            if self.credential:
                try:
                    await self.credential.close()
                    logger.debug("DefaultAzureCredential closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing DefaultAzureCredential: {str(e)}")
                finally:
                    self.credential = None

            # Clean up file locks
            async with self._file_locks_lock:
                self._file_locks.clear()

            self._is_initialized = False
            self._active_operations = 0

    def _ensure_initialized(self):
        """Ensure the service is properly initialized."""
        if not self._is_initialized or not self.blob_service_client:
            raise ServiceExecutionError("BlobService is not initialized. Use it within an async context manager.")

    async def _get_file_lock(self, file_path: str) -> asyncio.Lock:
        """Get or create a lock for a specific file path to prevent race conditions."""
        async with self._file_locks_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = asyncio.Lock()
            return self._file_locks[file_path]

    async def _safe_makedirs(self, directory_path: str) -> None:
        """Thread-safe directory creation."""
        try:
            # Use pathlib for better path handling and atomic directory creation
            Path(directory_path).mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            # Directory already exists, which is fine
            pass
        except Exception as e:
            logger.error(f"Failed to create directory '{directory_path}': {str(e)}")
            raise

    def get_container_client(self, container_name: str) -> ContainerClient:
        """Get a container client for the specified container."""
        self._ensure_initialized()
        return self.blob_service_client.get_container_client(container_name)
        
    async def test_connection(self) -> bool:
        """Test the connection to the Azure Blob Storage service."""
        try:
            await self.initialize()
            # Attempt to get service properties to verify connection
            props = await self.blob_service_client.get_service_properties()
            logger.debug("Connection test successful - service properties retrieved")
            return props is not None
        except Exception as e:
            error_msg = f"Failed to connect to Azure Blob Storage: {str(e)}"
            logger.error(error_msg)
            raise ServiceExecutionError(error_msg)

    async def download_file(self, container_name: str, filename: str, download_path: str) -> str:
        """
        Download a file from Azure Blob Storage with thread safety and atomic operations.
        Args:
            container_name (str): The name of the Azure Blob Storage container.
            filename (str): The name of the file to download from the container.
            download_path (str): The local file path where the downloaded file will be saved.
        Returns:
            str: The path where the file was downloaded (same as download_path parameter).
        Raises:
            ServiceExecutionError: If the container or blob doesn't exist, or if there are permission issues.
            OSError: If there are issues writing to the local file system.
        """
        # Normalize the download path to avoid issues with different path formats
        download_path = os.path.abspath(download_path)
        
        # Get a file-specific lock to prevent multiple threads from downloading the same file simultaneously
        file_lock = await self._get_file_lock(download_path)
        
        async with file_lock:
            try:
                async with self:
                    container_client = self.get_container_client(container_name)
                    blob_client = container_client.get_blob_client(filename)

                    logger.debug(f"Downloading blob '{filename}' from container '{container_name}' to '{download_path}'")
                
                    # Create directory if it doesn't exist (thread-safe)
                    directory_path = os.path.dirname(download_path)
                    if directory_path:
                        await self._safe_makedirs(directory_path)
                    
                    # Use a temporary file for atomic writes to prevent partial downloads
                    temp_file_suffix = f".tmp_{uuid.uuid4().hex}"
                    temp_download_path = download_path + temp_file_suffix
                    
                    try:
                        # Download to temporary file first
                        download_stream = await blob_client.download_blob()
                        with open(temp_download_path, "wb") as temp_file:
                            async for chunk in download_stream.chunks():
                                temp_file.write(chunk)
                        
                        # Atomic move from temporary file to final location
                        os.rename(temp_download_path, download_path)
                        
                        logger.debug(f"Successfully downloaded '{filename}' to '{download_path}'")
                        return download_path
                    
                    except Exception as e:
                        # Clean up temporary file if download failed
                        if os.path.exists(temp_download_path):
                            try:
                                os.remove(temp_download_path)
                            except OSError as cleanup_error:
                                logger.warning(f"Failed to clean up temporary file '{temp_download_path}': {cleanup_error}")
                        raise e
                
            except Exception as e:
                error_msg = f"Failed to download file '{filename}' from container '{container_name}': {str(e)}"
                logger.error(error_msg)
                raise ServiceExecutionError(error_msg)

    async def upload_file(self, container_name: str, filename: str, file_content) -> str:
        """
        Upload a file to Azure Blob Storage with improved error handling and retry logic.
        Args:
            container_name (str): The name of the Azure Blob Storage container.
            filename (str): The name of the file to upload to the container.
            file_content: The content of the file to upload (can be bytes, string, or file-like object).
        Returns:
            str: The URL of the uploaded blob.
        Raises:
            ServiceExecutionError: If the upload fails due to permission issues or other errors.
        """
        max_retries = 3
        retry_delay = 1.0  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                async with self:
                    container_client = self.get_container_client(container_name)

                    logger.debug(f"Uploading blob '{filename}' to container '{container_name}' (attempt {attempt + 1})")

                    blob_client = await container_client.upload_blob(
                        name=filename, 
                        data=file_content, 
                        overwrite=True,  # Allow overwriting existing blobs
                        timeout=300  # 5 minute timeout for large files
                    )
                    
                    blob_url = blob_client.url
                    logger.debug(f"Successfully uploaded '{filename}' to container '{container_name}' at URL: {blob_url}")
                    
                    return blob_url
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Upload attempt {attempt + 1} failed for '{filename}': {str(e)}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_msg = f"Failed to upload file '{filename}' to container '{container_name}' after {max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise ServiceExecutionError(error_msg)
                

    async def file_exists(self, container_name: str, filename: str) -> bool:
        """
        Check if a file exists in the Azure Blob Storage container.
        Args:
            container_name (str): The name of the Azure Blob Storage container.
            filename (str): The name of the file to check.
        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            await self.initialize()
            container_client = self.get_container_client(container_name)
            blob_client = container_client.get_blob_client(filename)
            
            # Check if blob exists by getting its properties
            await blob_client.get_blob_properties()
            return True
        except Exception:
            # If any exception occurs (including blob not found), return False
            return False
    
    