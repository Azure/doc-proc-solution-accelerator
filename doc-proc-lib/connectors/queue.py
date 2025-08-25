import logging

from azure.identity import ManagedIdentityCredential, AzureCliCredential, ChainedTokenCredential
from azure.core.exceptions import ResourceNotFoundError, AzureError

from azure.storage.queue import QueueClient
from configuration import Configuration

from .azure_client import AzureClient

class BlobQueueClient(AzureClient):

    def __init__(self):

        self.queue_client = None

        config = Configuration()

        self.storage_account_name = config.get_value("STORAGE_ACCOUNT_NAME")
        self.queue_name = config.get_value("QUEUE_NAME", 'docproc-requests')

        queue_url = f"https://{self.storage_account_name}.queue.core.windows.net"
        self.queue_client = QueueClient(queue_url, self.queue_name, credential=config.credential)

    async def send_message(self, message: str):
        try:
            self.queue_client.send_message(message)
        except Exception as ex:
            logging.error(ex)

    async def receive_messages(self, max_messages=5, visibility_timeout=30, wait_time=5):
        messages = self.queue_client.receive_messages(
            max_messages=max_messages,
            visibility_timeout=visibility_timeout,
            timeout=wait_time
        )
        return messages

    async def delete_message(self, message):
        self.queue_client.delete_message(message)
