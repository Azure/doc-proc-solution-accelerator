import logging

from .source_base import SourceBase

from doc.proc.service import ServiceBase, ServiceExecutionError, BlobService
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from dependencies import get_config

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

logger = logging.getLogger("doc.proc.source.blob") # need to specify the logger name as this module is loaded dynamically

class BlobSource(SourceBase):
    """Data source for loading data from Azure Blob Storage."""
    def __init__(self, name, type, settings: dict):
        super().__init__(name, type, settings)

        self.container_name = settings.get("container_name")
        self.file_types = settings.get("file_types", [])
        self.paths = settings.get("paths")
        self.include_metadata = settings.get("include_metadata", False)
        self.recursive = settings.get("recursive", False)
        self.config = get_config()
        self.storage_account_name = settings.get('account_name')
        self.account_url = f"https://{self.storage_account_name}.blob.core.windows.net"

        self.blob_service = BlobService(
            name="BlobService",
            type="blob_service",
            settings=settings
        )

    async def load_data(self) -> StepInputOutput:
        """Load data from Azure Blob Storage."""
        input_output = StepInputOutput()
        input_output.id = self.container_name
        input_output.summary_data = {}
        input_output.data = {}
        input_output.data["documents"] = []

        # Implement data loading logic from Azure Blob Storage here
        await self.blob_service._connect()
        container_client = await self.blob_service.get_container_client(self.container_name)
        
        # Process each blob
        async for blob in container_client.list_blobs():

            #check if blob has file type
            if not self.file_types or any(blob.name.endswith(ext) for ext in self.file_types):

                id = self.generate_sha1_hash(f"{self.name}/{self.type}/{self.container_name}/{blob.name}")
                
                item = {
                    "id": id,
                    "url": f"{self.account_url}/{self.container_name}/{blob.name}",
                    "parent_id": id,
                    "source_name": self.name,
                    "source_type": self.type,
                    "name": blob.name,
                    "size": blob.size,
                    "modified": blob.last_modified,
                    "created": blob.creation_time,
                    "content_uri": f"{self.name}/{self.type}/{self.container_name}/{blob.name}",
                    "file_path": f"{self.account_url}/{self.container_name}/{blob.name}",
                    "metadata" : {}
                }

                input_output.data["documents"].append(item)

        return input_output
    
    async def get_content(self, content_uri):
        """Get the content of a blob from Azure Blob Storage."""
        try:
            vals = content_uri.split('/')
            container_name = vals[2]
            blob_name = '/'.join(vals[3:])
            container_client = await self.blob_service.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            content = await blob_client.download_blob()
            return await content.readall()
        except Exception as e:
            logger.error(f"Failed to get content from Azure Blob Storage: {e}")
            return None
        
    async def get_content_metadata(self, content_uri):
        try:
            vals = content_uri.split('/')
            container_name = vals[2]
            blob_name = '/'.join(vals[3:])
            container_client = await self.blob_service.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            properties = await blob_client.get_blob_properties()
            id = self.generate_sha1_hash(content_uri)
            return {
                "id" : id,
                "parent_id": id,
                "source": self.name,
                "title": properties.name,
                "name": properties.name,
                "size": properties.size,
                #"content_type": properties.content_type,
                "last_modified": properties.last_modified
            }
        except Exception as e:
            logger.error(f"Failed to get content metadata from Azure Blob Storage: {e}")
            return {}

    async def get_content_security(self, content_uri):
        return {
            "metadata_security_id" : []
        }
    
    async def test_connection(self) -> bool:
        """Test the connection to Azure Blob Storage."""
        try:
            await self.blob_service.test_connection()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Azure Blob Storage: {e}")
            return False