import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.storage.queue.aio import QueueClient

from app.models.vault import DocumentInfo, Vault
from app.utils import get_azure_credential


logger = logging.getLogger("doc-proc-ui.app.services.storage_queue_helper")

class StorageQueueHelper():

    def __init__(self, storage_queue_url: str, queue_name: str):

        self.storage_queue_url = storage_queue_url
        self.queue_name = queue_name
        self._queue_client: QueueClient = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Connect to Azure Storage Queue"""
        try:
            self._queue_client = QueueClient(account_url=self.storage_queue_url, 
                                             queue_name=self.queue_name, 
                                             credential=get_azure_credential())
            
            # Verify connection by fetching queue properties
            await self._queue_client.get_queue_properties()
            logger.info(f"Connected to Azure Storage Queue: {self.queue_name}")

        except Exception as e:
            logger.error(f"Failed to connect to Azure Storage Queue: {e}. Ensure network connectivity and rbac permissions are set for the storage account.")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Azure Storage Queue"""
        if self._queue_client:
            await self._queue_client.close()
            self._queue_client = None
            logger.info("Disconnected from Azure Storage Queue")


    async def queue_documents_for_processing(self, vault: Vault, pipeline_to_process_documents: str, documents: List[DocumentInfo]) -> str:
        """
        Queue documents for processing
        """
        
        if not pipeline_to_process_documents:
            raise ValueError("pipeline_to_process_documents is required")
        
        if not documents and len(documents) == 0:
            raise ValueError("Documents list cannot be empty")
                
        # Create documents info list
        _documents = [{"id": doc.id, "blob_details": {**doc.blob_details}} for doc in documents if doc.id and doc.blob_details]

        logger.info(f"Queueing {len(_documents)} documents in vault '{vault.name}' for processing in pipeline '{pipeline_to_process_documents}'")

        # create message content
        message = {
            "message_type": "batch_execution_request",
            "pipeline_name": pipeline_to_process_documents,
            "vault_id": vault.id,
            "documents": _documents,
            "batch_id": f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:6]}_{len(_documents)}_docs",
            "priority": 0,
            "metadata": {
                "source": "vault_document_processing",
                "document_count": len(_documents),
                "vault_name": vault.name,
                "save_pipeline_step_outputs": vault.processing_config.save_pipeline_step_outputs if vault.processing_config else False
            },
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": "system",
            "correlation_id": str(uuid.uuid4())
        }

        msg_id = await self._send_message(message)

        logger.debug(f"Queued documents for processing with message ID: {msg_id}")
        
        return {"message_id": msg_id, "batch_id": message["batch_id"], "correlation_id": message["correlation_id"]}


    async def _send_message(self, message: Dict[str, Any], 
                            visibility_timeout: Optional[int] = None,
                            time_to_live: Optional[int] = None) -> str:
        """
        Send a message to the queue

        Args:
            message: Message content as dictionary
            visibility_timeout: Seconds before message becomes visible
            time_to_live: Message TTL in seconds (default: 7 days)

        Returns:
            Message ID
        """
        
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first or use in an async context.")
        
        try:
            message_content = json.dumps(message)
            response = await self._queue_client.send_message(
                content=message_content,
                visibility_timeout=visibility_timeout,
                time_to_live=time_to_live or 604800  # 7 days default
            )
            
            logger.debug(f"Sent message to queue: {response.id}")
            return response.id
            
        except Exception as e:
            logger.error(f"Failed to send message to queue: {e}")
            raise