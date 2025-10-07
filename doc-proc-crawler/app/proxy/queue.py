import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.storage.queue.aio import QueueClient

from doc.proc.providers.credential_provider import get_azure_credential


logger = logging.getLogger("doc-proc-crawler.proxy.queue")

class StorageQueue():

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

    async def send_message(self, message: Dict[str, Any], 
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