import logging
import datetime
import os
import time

from azure.storage.blob import ContainerClient, BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError, AzureError
from urllib.parse import urlparse, unquote
from typing import Union, IO

from dependencies import get_config
from configuration import Configuration
from .azure_client import AzureClient

class AzureBlobClient(AzureClient):
    def __init__(self,credential=None):
        # 1. Generate the credential in case it is not provided
        self.credential = self._get_credential(credential)
        self.blob_service_client = None

        config = get_config()

        self.storage_account_name = config.get_value("STORAGE_ACCOUNT_NAME")
        self.use_sas_token = config.get_value("USE_SAS_TOKEN", "true") == "true"
        self.hours = int(config.get_value("SAS_TOKEN_EXPIRY_HOURS", "1"))

        # Create BlobServiceClient using Managed Identity
        self.blob_service_client = BlobServiceClient(
            f"https://{self.storage_account_name}.blob.core.windows.net", credential=config.credential
        )

    def generate_sas_token(self, container_name, blob_name):
        delegation_key = self.blob_service_client.get_user_delegation_key(
            key_start_time=datetime.datetime.utcnow(),
            key_expiry_time=datetime.datetime.utcnow() + datetime.timedelta(hours=self.hours)
        )
        
        """Generate a SAS token with read & write access for a blob."""
        sas_token = generate_blob_sas(
            account_name=self.storage_account_name,
            container_name=container_name,
            blob_name=blob_name,
            user_delegation_key=delegation_key,  # Managed Identity handles authentication
            permission=BlobSasPermissions(read=True, write=True),  # Read & Write
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=self.hours)  # 1-hour expiry
        )

        blob_client = self.blob_service_client.get_blob_client(container_name, blob_name)

        if self.use_sas_token == "true" or self.use_sas_token == True:
            # Generate a SAS URL for the blob
            return f"{blob_client.url}?{sas_token}"
        else:
            # Generate a URL without SAS token for Managed Identity access
            return blob_client.url
        
    async def file_exists_async(self, container_name, blob_name):
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        try:
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False
        
    def get_files(self, container_name : str, path : str):
        container_client = self.blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs(name_starts_with=path)
        return blobs

    async def write_file_async(self, container_name, blob_name, data: bytes):
        return await self.upload_blob(container_name, blob_name, data)

    async def read_file_async(self, container_name, blob_name):
        return self.download_blob(container_name, blob_name)
        
    def download_blob(self, container_name, blob_name):
        """
        Downloads the blob data from Azure Blob Storage.

        Returns:
            bytes: The content of the blob.

        Raises:
            Exception: If downloading the blob fails after retries.
        """
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        data = b""

        try:
            logging.debug(f"[blob][{blob_name}] Attempting to download blob.")
            data = blob_client.download_blob().readall()
            logging.info(f"[blob][{blob_name}] Blob downloaded successfully.")
        except Exception as e:
            error_message = f"Error when downloading blob: {e}"            
            logging.error(f"[blob][{blob_name}] Failed to download blob. Error: {e}")
            raise Exception(error_message)

        return data
        
    async def upload_blob(self, container_name, blob_name, data: bytes):
        """
        Uploads a blob to Azure Blob Storage.

        :param data: The content of the blob to upload
        """
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        try:
            blob_client.upload_blob(data, overwrite=True)
            logging.info(f"[blob][{blob_name}] Blob uploaded successfully.")
        except Exception as e:
            logging.error(f"[blob][{blob_name}] Failed to upload blob. Error: {e}")
            raise


class BlobClient(AzureBlobClient):
    
    def __init__(self, blob_url, credential=None):
        """
        Initialize BlobClient with a specific blob URL.
        
        :param blob_url: URL of the blob (e.g., "https://mystorage.blob.core.windows.net/mycontainer/myblob.png")
        :param credential: Credential for authentication (optional)
        """
        super().__init__(credential)

        self.file_url = blob_url

        # 2. Parse the blob URL => account_url, container_name, blob_name
        try:
            parsed_url = urlparse(self.file_url)
            self.account_url = f"{parsed_url.scheme}://{parsed_url.netloc}"   # e.g. https://mystorage.blob.core.windows.net
            self.container_name = parsed_url.path.split("/")[1]              # e.g. 'mycontainer'
            # Blob name is everything after "/{container_name}/"
            self.blob_name = unquote(parsed_url.path[len(f"/{self.container_name}/"):])
            logging.debug(f"[blob][{self.blob_name}] Parsed blob URL successfully.")
        except Exception as e:
            logging.error(f"[blob] Invalid blob URL '{self.file_url}': {e}")
            raise EnvironmentError(f"Invalid blob URL '{self.file_url}': {e}")

    async def file_exists_async(self):
        return super().file_exists_async(self.container_name, self.blob_name)

    async def read_file_async(self):
        return await self.download_blob()

    async def write_file_async(self, data: bytes):
        await self.upload_blob(data)

    def upload_blob(self, data: bytes):
        super().upload_blob(self.container_name, self.blob_name, data)

    def download_blob(self):
        return super().download_blob(self.container_name, self.blob_name)

class BlobContainerClient(AzureBlobClient):
    def __init__(self, storage_account_base_url, container_name, credential=None):
        """
        Initialize BlobContainerClient with the storage account base URL and container name.
        
        :param storage_account_base_url: Base URL of the storage account (e.g., "https://mystorage.blob.core.windows.net")
        :param container_name: Name of the container
        :param credential: Credential for authentication (optional)
        """
        super().__init__(credential)
        
        try:
            self.container_client = ContainerClient(
                account_url=storage_account_base_url,
                container_name=container_name,
                credential=self.credential
            )
            # Verify the container exists
            self.container_client.get_container_properties()
            logging.debug(f"[blob] Connected to container '{container_name}'.")
        except ResourceNotFoundError:
            logging.error(f"[blob] Container '{container_name}' does not exist.")
            raise
        except AzureError as e:
            logging.error(f"[blob] Failed to connect to container: {e}")
            raise
        
    def upload_blob(self, blob_name : str, file_path : str, overwrite:bool=False):
        """
        Upload a local file to a blob within the container.
        
        :param blob_name: Name of the blob
        :param file_path: Path to the local file to upload
        :param overwrite: Whether to overwrite the blob if it already exists
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=overwrite)
            logging.info(f"[blob] Uploaded '{file_path}' as blob '{blob_name}'.")
        except AzureError as e:
            logging.info(f"[blob] Failed to upload blob '{blob_name}': {e}")

    def upload_blob(self, blob_name : str, file_bytes : bytes, overwrite:bool=False):
        """
        Upload a local file to a blob within the container.
        
        :param blob_name: Name of the blob
        :param file_bytes: File bytes to upload
        :param overwrite: Whether to overwrite the blob if it already exists
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file_bytes, overwrite=overwrite)
            logging.info(f"[blob] Uploaded '{blob_name}' as blob '{blob_name}'.")
        except AzureError as e:
            logging.info(f"[blob] Failed to upload blob '{blob_name}': {e}")

    def download_blob(self, blob_name, download_file_path):
        """
        Download a blob from the container to a local file.
        
        :param blob_name: Name of the blob
        :param download_file_path: Path to the local file where the blob will be downloaded
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(download_file_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            logging.info(f"[blob] Downloaded blob '{blob_name}' to '{download_file_path}'.")
        except ResourceNotFoundError:
            logging.info(f"[blob] Blob '{blob_name}' not found in container '{self.container_client.container_name}'.")
        except AzureError as e:
            logging.info(f"[blob] Failed to download blob '{blob_name}': {e}")

    def delete_blob(self, blob_name):
        """
        Delete a blob from the container.
        
        :param blob_name: Name of the blob to delete
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logging.info(f"[blob] Deleted blob '{blob_name}' from container '{self.container_client.container_name}'.")
        except ResourceNotFoundError:
            logging.info(f"[blob] Blob '{blob_name}' not found in container '{self.container_client.container_name}'.")
        except AzureError as e:
            logging.info(f"[blob] Failed to delete blob '{blob_name}': {e}")

    def list_blobs(self, generate_sas_token=False, path=None) -> list:
        """
        List all blobs in the container.
        
        :return: List of blob names
        """
        data = []
        try:
            blobs = self.container_client.list_blobs()
            blob_names = [blob.name for blob in blobs]
            logging.debug(f"Blobs in container '{self.container_client.container_name}':")
            for name in blob_names:
                logging.debug(f" - {name}")
            
            if generate_sas_token:
                response = ''
                for blob_name in blob_names:
                    sas_url = self.generate_sas_token(self.container_client.container_name, blob_name)
                    data.append(sas_url)
                return data
            else:
                return blob_names

        except AzureError as e:
            return []

    def _invalidate_container(self, container_name: str):
        container_client = self.blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()

    def _get_container_client(self, container_name=None):
        if container_name:
            full_container_name = (
                f"{self.parent_container_name}/{container_name}"
                if self.parent_container_name
                else container_name
            )
        elif self.parent_container_name is not None and container_name is None:
            full_container_name = self.parent_container_name
        else:
            raise ValueError(
                "Container name must be provided either during initialization or as a function argument."
            )

        container_client = self.blob_service_client.get_container_client(
            full_container_name
        )

        return container_client

    def upload_file(self, container_name: str, blob_name: str, file_path: str):
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    def upload_stream(self, container_name: str, blob_name: str, stream: IO):
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )

        blob_client.upload_blob(stream, overwrite=True)

    def upload_text(self, container_name: str, blob_name: str, text: str):
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )
        blob_client.upload_blob(text, overwrite=True)

    def download_file(self, container_name: str, blob_name: str, download_path: str):
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )
        with open(download_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())

    def download_stream(self, container_name: str, blob_name: str) -> bytes:
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )
        stream = blob_client.download_blob().readall()
        return stream

    def download_text(self, container_name: str, blob_name: str) -> str:
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )
        text = blob_client.download_blob().content_as_text()
        return text

    def delete_blob(self, container_name: str, blob_name: str):
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )
        blob_client.delete_blob()

    def update_blob(
        self, container_name: str, blob_name: str, data: Union[str, IO, bytes]
    ):
        self.upload_blob(container_name, blob_name, data)

    def upload_blob(
        self, container_name: str, blob_name: str, data: Union[str, IO, bytes]
    ):
        blob_client = self._get_container_client(container_name).get_blob_client(
            blob_name
        )
        if isinstance(data, str):
            blob_client.upload_blob(data, overwrite=True)
        elif isinstance(data, bytes):
            blob_client.upload_blob(data, overwrite=True)
        elif hasattr(data, "read"):
            blob_client.upload_blob(data, overwrite=True)
        else:
            raise ValueError("Unsupported data type for upload")
