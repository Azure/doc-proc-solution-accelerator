import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.storage.blob.aio import BlobServiceClient

from doc.proc.providers.credential_provider import get_azure_credential

from app.db.cosmos import CosmosDb
from app.services.base import BaseService
from app.services.document_queue_submitter import DocumentQueueSubmitter
from app.models.vault import ContentIdentifierInfo, Vault, DocumentInfo, PaginatedResponse

logger = logging.getLogger("doc-proc-ui.app.services.vault_documents_service")

class VaultDocumentsService(BaseService):

    def __init__(self, db: CosmosDb,
                       container_name: str = "vault_documents",
                       document_queue_submitter: DocumentQueueSubmitter = None):

        super().__init__(db, container_name)
        self.document_queue_submitter = document_queue_submitter
        self._operations_lock = asyncio.Lock()

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
        unique_id = "doc_" + uuid.uuid4().hex[:8]
        document = DocumentInfo(
            id=unique_id,
            vault_id=vault.id,
            name=file_name,
            content_id=ContentIdentifierInfo(
                canonical_id=f'azure_blob://{vault.storage_config.account_name}/{vault.storage_config.container_name}/{file_name_to_upload}',
                unique_id=unique_id,
                source_id=vault.id, #TODO: make this come from default vault source
                source_name=vault.default_source_instance_name,
                source_type="azure_blob",
                container=vault.storage_config.container_name,
                path=file_name_to_upload,
                metadata={}
            ),
            submit_date=datetime.now(timezone.utc).isoformat(),
            source="user_upload",
        )

        logger.debug(f"Adding document record to database: {document}")

        await self.create(document.model_dump())

        return document
    
    async def queue_documents_for_processing(self, vault: Vault, documents: List[DocumentInfo]) -> List[DocumentInfo]:
        """Queue documents for processing by updating their status to 'queued'"""
        if not vault or not documents or len(documents) == 0:
            raise ValueError("Vault and DocumentInfo list are required")

        logger.debug(f"Queuing documents '{len(documents)}' in vault '{vault.name}' for processing")

        # send the documents in batches of batch_size to the storage queue
        # TODO: make batch size configurable
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            try:
                async with self._operations_lock:
                    async with self.document_queue_submitter:
                        _queue_result = await self.document_queue_submitter.queue_documents_for_processing(vault=vault,
                                                                                                        pipeline_to_process_documents=vault.pipeline_name,
                                                                                                        documents=batch)

                logger.info(f"Queued {len(batch)} documents for processing in vault '{vault.name}' with message ID: {_queue_result['message_id']}")

                for document in batch:
                    document.status = "queued"
                    document.metadata["pipeline_name"] = vault.pipeline_name
                    document.metadata["queue_message_id"] = _queue_result["message_id"]
                    document.metadata["correlation_id"] = _queue_result["correlation_id"]
                    document.metadata["batch_id"] = _queue_result["batch_id"]
                    document.metadata["processing_attempts"] = (document.metadata.get("processing_attempts", 0) + 1)
                    document.metadata["error"] = None
                    document.metadata["error_details"] = None
                    document.metadata["last_processing_attempt"] = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                logger.error(f"Failed to queue documents for processing in vault '{vault.name}': {str(e)}")
                
                # update the document status to 'error'
                for document in batch:
                    document.status = "error"
                    document.metadata["error"] = "Failed to queue document for processing. Check app health and connection to Azure Storage Queue. Check logs for details."
                    document.metadata["error_details"] = str(e)
                    document.metadata["processing_attempts"] = (document.metadata.get("processing_attempts", 0) + 1)
                    document.metadata["last_processing_attempt"] = datetime.now(timezone.utc).isoformat()
                    document.metadata["pipeline_name"] = vault.pipeline_name


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
        """Get all documents for a vault"""
        if not vault_id:
            raise ValueError("vault_id is required")

        # Build the base query and parameters for filtering
        _query = "SELECT * FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]

        # Execute the query to get documents
        items = await self.list_all(_query, parameters)
        documents = [DocumentInfo(**item) for item in items]
        
        return documents


    async def get_vault_documents_paginated(self, 
                                            vault_id: str, 
                                            page: int = 1, 
                                            page_size: int = 20,
                                            time_filter: Optional[str] = None,
                                            search: Optional[str] = None,
                                            sort_by: Optional[str] = None,
                                            sort_direction: Optional[str] = None) -> PaginatedResponse[DocumentInfo]:
        """Get documents for a vault with pagination"""
        if not vault_id:
            raise ValueError("vault_id is required")

        # Build the base query and parameters for filtering
        base_query = "SELECT * FROM c WHERE c.vault_id = @vault_id"
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]

        # Add time filter
        if time_filter and time_filter != 'all':
            # Calculate the cutoff datetime based on time_filter
            now = datetime.now(timezone.utc)
            time_deltas = {
                "1h": timedelta(hours=1),
                "4h": timedelta(hours=4),
                "24h": timedelta(days=1),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30)
            }
            
            if time_filter not in time_deltas:
                time_filter = "24h"  # Default fallback

            cutoff_time = now - time_deltas[time_filter]
            cutoff_timestamp = cutoff_time.isoformat()
            
            base_query += " AND c.submit_date >= @cutoff_time"
            count_query += " AND c.submit_date >= @cutoff_time"
            parameters.append({"name": "@cutoff_time", "value": cutoff_timestamp})

        # Add search filter
        if search:
            base_query += " AND CONTAINS(c.name, @search)"
            count_query += " AND CONTAINS(c.name, @search)"
            parameters.append({"name": "@search", "value": search})

        # Get total count first
        count_result = await self.list_all(count_query, parameters)
        total_count = count_result[0] if count_result and len(count_result) > 0 else 0

        # Add sorting to base query
        if sort_by:
            valid_sort_fields = ["name", "submit_date", "source", "status", "content_type"]
            if sort_by in valid_sort_fields:
                base_query += f" ORDER BY c.{sort_by} {sort_direction or 'ASC'}"
            else:
                base_query += " ORDER BY c.submit_date DESC"  # Default sort
        else:
            base_query += " ORDER BY c.submit_date DESC"  # Default sort

        # Add pagination
        offset = (page - 1) * page_size
        base_query += f" OFFSET {offset} LIMIT {page_size}"

        # Execute the query to get documents
        items = await self.list_all(base_query, parameters)
        documents = [DocumentInfo(**item) for item in items]

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

        # Return paginated response
        return PaginatedResponse[DocumentInfo](
            items=documents,
            total=total_count,
            page=page,
            pageSize=page_size,
            totalPages=total_pages
        )


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


    async def delete_documents_in_vault(self, vault_id: str) -> int:
        """Delete all documents in a vault"""
        if not vault_id:
            raise ValueError("vault_id is required")

        # Get all documents in the vault
        documents = await self.get_vault_documents(vault_id)
        if not documents or len(documents) == 0:
            logger.info(f"No documents found in vault '{vault_id}' to delete")
            return 0

        # Delete each document record from the database
        delete_tasks = [self.delete(document.id) for document in documents]
        await asyncio.gather(*delete_tasks)

        logger.info(f"Deleted {len(documents)} documents from vault '{vault_id}'")
        return len(documents)