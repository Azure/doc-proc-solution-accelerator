import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.storage.blob.aio import BlobServiceClient

from app.db.cosmos import CosmosDb
from app.utils import get_azure_credential
from app.services.base import BaseService
from app.services.storage_queue_helper import StorageQueueHelper
from app.models.vault import AddDocumentRequest, Vault, DocumentInfo

logger = logging.getLogger("doc-proc-ui.app.services.vault_documents_service")

class VaultDocumentsService(BaseService):

    def __init__(self, db: CosmosDb,
                       container_name: str = "vault_documents",
                       storage_queue_helper: StorageQueueHelper = None):

        super().__init__(db, container_name)
        self.storage_queue_helper = storage_queue_helper

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate vault document item"""
        required_fields = ["id", "vault_id", "name", "blob_url", "size_bytes", "uploaded_at"]
        return all(field in item for field in required_fields)

    async def add_file(self, vault: Vault, file_name:str, file_contents: bytes, file_content_type: str, overwrite: bool=False) -> Any:
        """Add a document to a vault"""
        if not vault:
            raise ValueError("Vault is required")

        if not file_name:
            raise ValueError("file_name is required")
        
        if not vault.storage_config or not vault.storage_config.account_name or not vault.storage_config.container_name:
            raise ValueError(f"Vault with ID '{vault.id}' does not have complete storage configuration")
        
        # check of file already exists in the vault
        existing_doc = await self.get_vault_document(vault.id, document_name=file_name)
        if existing_doc:
            if overwrite:
                logger.info(f"Document with name '{file_name}' already exists in vault '{vault.name}'. Overwriting as requested.")
                # delete the existing document record in Cosmos DB
                await self.delete(existing_doc.id)
            else:
                logger.warning(f"Document with name '{file_name}' already exists in vault '{vault.name}'")
                raise FileExistsError(f"Document with name '{file_name}' already exists in vault '{vault.name}'")
        
        file_size = len(file_contents)
        file_name_to_upload = f"{vault.name.replace(' ', '_')}/{file_name.replace(' ', '-')}"

        # write the file to the blob storage
        blob_url = await self._upload_file_to_blob_storage(vault.storage_config.model_dump(), file_name_to_upload, file_contents, file_content_type)
        if not blob_url:
            raise ValueError("Failed to upload file to blob storage")

        # add an entry to the documents collection in cosmos db
        document = DocumentInfo(
            id="doc_" + uuid.uuid4().hex[:8],
            vault_id=vault.id,
            name=file_name,
            blob_url=blob_url,
            blob_details={
                "storage_account": vault.storage_config.account_name,
                "container": vault.storage_config.container_name,
                "blob": file_name_to_upload
            },
            size_bytes=file_size,
            content_type=file_content_type,
            upload_date=datetime.now(timezone.utc).isoformat()
        )

        logger.debug(f"Adding document record to database: {document}")

        await self.create(document.model_dump())

        return document
    
    async def add_document(self, vault: Vault, document: AddDocumentRequest) -> DocumentInfo:
        """Add a document to a vault"""

        if not vault:
            raise ValueError("Vault is required")

        if not document or not document.name or not document.blob_url:
            raise ValueError("Document with valid name and blob_url must be provided")

        logger.debug(f"Adding document '{document.name}' to vault '{vault.id}' from blob URL '{document.blob_url}'")

        # add an entry to the documents collection in cosmos db
        added_document = DocumentInfo(
            id="doc_" + uuid.uuid4().hex[:8],
            vault_id=vault.id,
            name=document.name,
            blob_url=document.blob_url,
            blob_details={
                "storage_account": vault.storage_config.account_name,
                "container": vault.storage_config.container_name,
                "blob": document.name
            },
            size_bytes=0,
            content_type="unknown",
            source=document.source,
            metadata=document.metadata or {},
            upload_date=datetime.now(timezone.utc).isoformat()
        )
        
        logger.debug(f"Adding document record to database: {added_document}")

        await self.create(added_document.model_dump())

        return added_document


    async def queue_documents_for_processing(self, vault: Vault, documents: List[DocumentInfo]) -> List[DocumentInfo]:
        """Queue documents for processing by updating their status to 'queued'"""
        if not vault or not documents or len(documents) == 0:
            raise ValueError("Vault and DocumentInfo list are required")

        logger.debug(f"Queuing documents '{len(documents)}' in vault '{vault.name}' for processing")

        # send the documents in batches of 10 to the storage queue
        # TODO: make batch size configurable
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            async with self.storage_queue_helper:
                _queue_result = await self.storage_queue_helper.queue_documents_for_processing(vault.pipeline_name, batch)
                logger.info(f"Queued {len(batch)} documents for processing in vault '{vault.name}' with message ID: {_queue_result['message_id']}")

        for document in documents:
            document.status = "queued"
            document.metadata["processing_attempts"] = (document.metadata.get("processing_attempts", 0) + 1)
            document.metadata["last_processing_attempt"] = datetime.now(timezone.utc).isoformat()
            document.metadata["pipeline_name"] = vault.pipeline_name
            document.metadata["queue_message_id"] = _queue_result["message_id"]
            document.metadata["correlation_id"] = _queue_result["correlation_id"]
            document.metadata["batch_id"] = _queue_result["batch_id"]

        # Update the document records in the database
        await self.batch_upsert([document.model_dump() for document in documents])

        return documents

    async def get_vault_document(self, vault_id: str, document_id: Optional[str] = None, document_name: Optional[str] = None) -> Optional[DocumentInfo]:
        """Get a document for a vault"""
        if not vault_id:
            raise ValueError("vault_id is required")

        if document_id:
            query = f"SELECT * FROM c WHERE c.vault_id = @vault_id AND c.id = @document_id"
            parameters = [
                {"name": "@vault_id", "value": vault_id},
                {"name": "@document_id", "value": document_id}
            ]
            items = await self.list_all(query, parameters)
            if items:
                return DocumentInfo(**items[0])
            else:
                return None
        elif document_name:
            query = f"SELECT * FROM c WHERE c.vault_id = @vault_id AND c.name = @document_name"
            parameters = [
                {"name": "@vault_id", "value": vault_id},
                {"name": "@document_name", "value": document_name}
            ]
            items = await self.list_all(query, parameters)
            if items:
                return DocumentInfo(**items[0])
            else:
                return None
        else:
            return None


    async def get_vault_documents(self, vault_id: str) -> List[DocumentInfo]:
        """Get documents for a vault"""
        if not vault_id:
            raise ValueError("vault_id is required")

        query = f"SELECT * FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]

        items = await self.list_all(query, parameters)
        documents = [DocumentInfo(**item) for item in items]

        return documents

    async def _upload_file_to_blob_storage(self, storage_config: Dict[str, Any], file_name: str, file_contents: bytes, content_type: str) -> str:
        """Upload a file to Azure Blob Storage."""

        if not storage_config:
            raise ValueError("Storage configuration is required")

        if not storage_config.get("account_name", None):
            raise ValueError("Storage account name is required in storage configuration")

        if not storage_config.get("container_name", None):
            raise ValueError("Container name is required in storage configuration")

        if not file_name:
            raise ValueError("File name is required")

        if not file_contents:
            raise ValueError("File contents are required")

        # Construct the blob service client for the specified storage account
        blob_account_url = f"https://{storage_config['account_name']}.blob.core.windows.net"

        logger.debug(f"Uploading file to blob storage at account URL: {blob_account_url}, container: {storage_config.get('container_name')}, file: {file_name}")

        blob_service_client = BlobServiceClient(account_url=blob_account_url, credential=get_azure_credential())

        try:
            async with blob_service_client:
                # Instantiate a new ContainerClient
                container_client = blob_service_client.get_container_client(storage_config.get("container_name"))

                if not await container_client.exists():
                    logger.debug(f"Container '{storage_config.get('container_name')}' does not exist. Creating it.")
                    # Create new Container in the service
                    await container_client.create_container()

                blob_url = await self._upload_file_with_retries(container_client, file_name, file_contents)

            logger.debug(f"Blob '{file_name}' uploaded successfully")
            return blob_url
        except Exception as e:
            logger.error(f"Failed to upload blob '{file_name}': {str(e)}")
            raise e


    async def _upload_file_with_retries(self, container_client: str, filename: str, file_content) -> str:
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

                blob_client = await container_client.upload_blob(
                    name=filename,
                    data=file_content,
                    overwrite=True,  # Allow overwriting existing blobs
                    timeout=300  # 5 minute timeout for large files
                )

                blob_url = blob_client.url
                return blob_url

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Upload attempt {attempt + 1} failed for '{filename}': {str(e)}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_msg = f"Failed to upload file '{filename}' after {max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise e


    # async def file_exists(self, container_name: str, filename: str) -> bool:
    #     """
    #     Check if a file exists in the Azure Blob Storage container.
    #     Args:
    #         container_name (str): The name of the Azure Blob Storage container.
    #         filename (str): The name of the file to check.
    #     Returns:
    #         bool: True if the file exists, False otherwise.
    #     """
    #     try:
    #         await self.initialize()
    #         container_client = self.get_container_client(container_name)
    #         blob_client = container_client.get_blob_client(filename)

    #         # Check if blob exists by getting its properties
    #         await blob_client.get_blob_properties()
    #         return True
    #     except Exception:
    #         # If any exception occurs (including blob not found), return False
    #         return False


    # async def download_file(self, container_name: str, filename: str, download_path: str) -> str:
    #     """
    #     Download a file from Azure Blob Storage with thread safety and atomic operations.
    #     Args:
    #         container_name (str): The name of the Azure Blob Storage container.
    #         filename (str): The name of the file to download from the container.
    #         download_path (str): The local file path where the downloaded file will be saved.
    #     Returns:
    #         str: The path where the file was downloaded (same as download_path parameter).
    #     Raises:
    #         ServiceExecutionError: If the container or blob doesn't exist, or if there are permission issues.
    #         OSError: If there are issues writing to the local file system.
    #     """
    #     # Normalize the download path to avoid issues with different path formats
    #     download_path = os.path.abspath(download_path)

    #     # Get a file-specific lock to prevent multiple threads from downloading the same file simultaneously
    #     file_lock = await self._get_file_lock(download_path)

    #     async with file_lock:
    #         try:
    #             async with self:
    #                 container_client = self.get_container_client(container_name)
    #                 blob_client = container_client.get_blob_client(filename)

    #                 logger.debug(f"Downloading blob '{filename}' from container '{container_name}' to '{download_path}'")

    #                 # Create directory if it doesn't exist (thread-safe)
    #                 directory_path = os.path.dirname(download_path)
    #                 if directory_path:
    #                     await self._safe_makedirs(directory_path)

    #                 # Use a temporary file for atomic writes to prevent partial downloads
    #                 temp_file_suffix = f".tmp_{uuid.uuid4().hex}"
    #                 temp_download_path = download_path + temp_file_suffix

    #                 try:
    #                     # Download to temporary file first
    #                     download_stream = await blob_client.download_blob()
    #                     with open(temp_download_path, "wb") as temp_file:
    #                         async for chunk in download_stream.chunks():
    #                             temp_file.write(chunk)

    #                     # Atomic move from temporary file to final location
    #                     os.rename(temp_download_path, download_path)

    #                     logger.debug(f"Successfully downloaded '{filename}' to '{download_path}'")
    #                     return download_path

    #                 except Exception as e:
    #                     # Clean up temporary file if download failed
    #                     if os.path.exists(temp_download_path):
    #                         try:
    #                             os.remove(temp_download_path)
    #                         except OSError as cleanup_error:
    #                             logger.warning(f"Failed to clean up temporary file '{temp_download_path}': {cleanup_error}")
    #                     raise e

    #         except Exception as e:
    #             error_msg = f"Failed to download file '{filename}' from container '{container_name}': {str(e)}"
    #             logger.error(error_msg)
    #             raise ServiceExecutionError(error_msg)