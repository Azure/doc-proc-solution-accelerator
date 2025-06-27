import logging
import os
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from .service_base import ServiceBase, ServiceExecutionError

logger = logging.getLogger(__name__)


class BlobService(ServiceBase):
    """Azure Blob Storage service for managing blob storage operations."""

    def __init__(self, name: str, type: str, **settings):
        super().__init__(name=name, type=type, **settings)

        self.storage_account_name = settings.get('account_name')
        self.credential_type = settings.get('credential_type')
        self.credential_key = ''

        # Validate storage account name
        if not self.storage_account_name:
            raise ValueError("Settings key 'account_name' is required")

        if self.storage_account_name.startswith('${') and self.storage_account_name.endswith('}'):
            env_var_name = self.storage_account_name[2:-1]
            self.storage_account_name = os.getenv(env_var_name)
            if not self.storage_account_name:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            raise ValueError("Settings key 'account_name' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")


        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        if self.credential_type.startswith('${') and self.credential_type.endswith('}'):
            env_var_name = self.credential_type[2:-1]
            self.credential_type = os.getenv(env_var_name)
            if not self.credential_type:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            raise ValueError("Settings key 'credential_type' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")


        # Validate credential key based on credential type
        if self.credential_type == 'azure_key_credential':
            self.credential_key = settings.get('credential_key')

            if not self.credential_key:
                raise ValueError("Settings key 'credential_key' is required for azure_key_credential")
            
            # Read the credential key from environment variable
            if self.credential_key.startswith('${') and self.credential_key.endswith('}'):
                env_var_name = self.credential_key[2:-1]
                self.credential_key = os.getenv(env_var_name)
                if not self.credential_key:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            else:
                raise ValueError("Settings key 'credential_key' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")

        elif self.credential_type == 'default_azure_credential':
            self.credential_key = ''
        
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}. Supported types are 'azure_key_credential' and 'default_azure_credential'.")
        
        self.blob_service_client: BlobServiceClient


    async def __aenter__(self):
        """Initialize the BlobServiceClient."""

        account_url = f"https://{self.storage_account_name}.blob.core.windows.net"

        logger.debug(f"Creating BlobServiceClient with account URL: {account_url} and credential type: {self.credential_type}")

        if self.credential_key not in ['', None]:
            self.blob_service_client = BlobServiceClient(account_url=account_url, credential=self.credential_key)
        else:
            async with DefaultAzureCredential() as credential:
                self.blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

        logger.debug(f"Initialized BlobServiceClient")

        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.blob_service_client.close()


    async def test_connection(self) -> bool:
        """Test the connection to the Azure Blob Storage service."""
        try:
            async with self.blob_service_client as client:
                # Attempt to get service properties to verify connection
               props = await client.get_service_properties()
               return props is not None
        except Exception as e:
            raise ServiceExecutionError(f"Failed to connect to Azure Blob Storage: {str(e)}")

        return False

    async def get_container_client(self, container_name:str):

        async with self.blob_service_client.get_container_client(container_name) as container_client:
            return container_client


    async def upload_file(self, container_name:str, filename:str, file_content):
        
        container_client = await self.get_container_client(container_name)

        file_blob_client = await container_client.upload_blob(name=filename, data=file_content, overwrite=False)

        return file_blob_client.url