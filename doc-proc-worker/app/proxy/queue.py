import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, HttpResponseError
from azure.storage.queue.aio import QueueClient


from doc.proc.providers.credential_provider import get_azure_credential

logger = logging.getLogger("doc-proc-worker.app.proxy.queue")

class QueueMessage:
    """Wrapper for queue message with automatic JSON handling"""
    
    def __init__(self, message):
        self._message = message
        self._content = None
        
    @property
    def content(self) -> Dict[str, Any]:
        """Get message content as parsed JSON"""
        if self._content is None:
            try:
                self._content = json.loads(self._message.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message content as JSON: {e}")
                raise ValueError(f"Invalid JSON in message: {e}")
        return self._content
    
    @property
    def id(self) -> str:
        """Get message ID"""
        return self._message.id
    
    @property
    def pop_receipt(self) -> str:
        """Get pop receipt for message deletion"""
        return self._message.pop_receipt
    
    @property
    def dequeue_count(self) -> int:
        """Get number of times message has been dequeued"""
        return self._message.dequeue_count
    
    @property
    def inserted_on(self) -> datetime:
        """Get message insertion time"""
        return self._message.inserted_on
    
    @property
    def expires_on(self) -> datetime:
        """Get message expiration time"""
        return self._message.expires_on


class StorageQueue():
    """Service for interacting with Azure Storage Queue"""
    
    def __init__(self, storage_account_queue_url: str,
                 queue_name: str):
        
        if not storage_account_queue_url:
            raise ValueError("Storage account queue URL is required")
        if not queue_name:
            raise ValueError("Queue name is required")
        
        self.storage_account_url = storage_account_queue_url
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
            self._queue_client = QueueClient(account_url=self.storage_account_url, 
                                             queue_name=self.queue_name, 
                                             credential=get_azure_credential())
            await self._queue_client.create_queue()
            logger.info(f"Connected to Azure Storage Queue: {self.queue_name}")

        except ResourceExistsError as e:
            logger.debug(f"Azure Storage Queue with the name: {self.queue_name} already exists.")
            logger.info(f"Connected to existing Azure Storage Queue: {self.queue_name}")
        # Check if we got an authorization error on creating the queue, as the client id might only be able to read the queue, not create it.
        except HttpResponseError as e:
            if 'AuthorizationFailure' in e.message or e.status_code == 403:
                logger.warning(f"Authorization error when accessing the queue: {e}. Attempting to connect to existing queue.")
                # Try to connect to the existing queue
                try:
                    props = await self._queue_client.get_queue_properties()
                    logger.info(f"Connected to existing Azure Storage Queue: {self.queue_name}")
                except Exception as inner_e:
                    logger.error(f"Failed to access existing queue: {inner_e}")
                    raise
            else:
                logger.error(f"HTTP error when connecting to Azure Storage Queue: {e}")
                raise
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
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
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
    
    async def receive_messages(self, max_messages: int = 1, 
                              visibility_timeout: int = 30) -> list[QueueMessage]:
        """
        Receive messages from the queue
        
        Args:
            max_messages: Maximum number of messages to receive (1-32)
            visibility_timeout: Seconds message is hidden from other consumers
            
        Returns:
            List of QueueMessage objects
        """
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
        try:
            # Ensure max_messages is within valid range
            max_messages = max(1, min(32, max_messages))
            
            messages = self._queue_client.receive_messages(
                max_messages=max_messages,
                visibility_timeout=visibility_timeout
            )
            
            wrapped_messages = [QueueMessage(msg) async for msg in messages]
            logger.debug(f"Received {len(wrapped_messages)} messages from queue")
            
            return wrapped_messages
            
        except Exception as e:
            logger.error(f"Failed to receive messages from queue: {e}")
            raise
    
    async def delete_message(self, message: QueueMessage) -> bool:
        """
        Delete a message from the queue
        
        Args:
            message: QueueMessage to delete
            
        Returns:
            True if deletion successful
        """
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
        try:
            await self._queue_client.delete_message(
                message=message.id,
                pop_receipt=message.pop_receipt
            )
            
            logger.debug(f"Deleted message from queue: {message.id}")
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Message not found for deletion: {message.id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete message from queue: {e}")
            raise
    
    async def update_message(self, message: QueueMessage, content: Dict[str, Any],
                            visibility_timeout: int = 0) -> bool:
        """
        Update message content and visibility
        
        Args:
            message: QueueMessage to update
            content: New message content
            visibility_timeout: New visibility timeout
            
        Returns:
            True if update successful
        """
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
        try:
            message_content = json.dumps(content)
            await self._queue_client.update_message(
                message=message.id,
                pop_receipt=message.pop_receipt,
                content=message_content,
                visibility_timeout=visibility_timeout
            )
            
            logger.debug(f"Updated message in queue: {message.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update message in queue: {e}")
            raise
    
    async def peek_messages(self, max_messages: int = 1) -> list[QueueMessage]:
        """
        Peek at messages without removing them from queue
        
        Args:
            max_messages: Maximum number of messages to peek (1-32)
            
        Returns:
            List of QueueMessage objects (without pop_receipt)
        """
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
        try:
            max_messages = max(1, min(32, max_messages))
            
            messages = await self._queue_client.peek_messages(max_messages=max_messages)
            wrapped_messages = [QueueMessage(msg) for msg in messages]
            
            logger.debug(f"Peeked at {len(wrapped_messages)} messages in queue")
            return wrapped_messages
            
        except Exception as e:
            logger.error(f"Failed to peek messages in queue: {e}")
            raise
    
    async def get_queue_properties(self) -> Dict[str, Any]:
        """Get queue properties including message count"""
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
        try:
            properties = await self._queue_client.get_queue_properties()
            return {
                "approximate_message_count": properties.approximate_message_count,
                "metadata": properties.metadata or {}
            }
        except Exception as e:
            logger.error(f"Failed to get queue properties: {e}")
            raise
    
    async def clear_queue(self) -> bool:
        """Clear all messages from the queue"""
        if not self._queue_client:
            raise RuntimeError("Queue client not connected. Call connect() first.")
        
        try:
            await self._queue_client.clear_messages()
            logger.info("Cleared all messages from queue")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            raise
