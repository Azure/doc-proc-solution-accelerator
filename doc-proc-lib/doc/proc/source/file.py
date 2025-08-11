import os
import logging

from .source_base import SourceBase

from doc.proc.service import ServiceBase, ServiceExecutionError, BlobService
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from dependencies import get_config

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

logger = logging.getLogger("doc.proc.source.file") # need to specify the logger name as this module is loaded dynamically

class FileSource(SourceBase):
    """Data source for loading data from local File Storage."""
    def __init__(self, name, type, settings: dict):
        super().__init__(name, type, settings)

        self.container_name = settings.get("container_name")
        self.file_types = settings.get("file_types", [])
        self.paths = settings.get("paths")
        self.include_metadata = settings.get("include_metadata", False)
        self.recursive = settings.get("recursive", False)
        self.config = get_config()

    async def load_data(self) -> StepInputOutput:
        """Load data from local File Storage."""
        input_output = StepInputOutput()
        input_output.id = self.container_name
        input_output.summary_data = {}
        input_output.data = {}
        input_output.data["documents"] = []

        # Implement data loading logic from local File Storage here
        # Process each file
        for root, dirs, files in os.walk(self.paths):
            for filename in files:
                if not self.file_types or any(filename.endswith(ext) for ext in self.file_types):
                    file_path = os.path.join(root, filename)
                    item = {
                        "source_name": self.name,
                        "source_type": self.type,
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path),
                        "created": os.path.getctime(file_path),
                        "content_uri": f"{self.name}/{self.type}/{self.container_name}/{filename}",
                        "file_path": file_path,
                        "metadata": {}
                    }

                    input_output.data["documents"].append(item)

        return input_output
    
    async def get_content(self, content_uri):
        """Get the content of a blob from Azure Blob Storage."""
        try:
            blob_client = await self.blob_service.get_blob_client(content_uri)
            content = await blob_client.download_blob()
            return await content.readall()
        except Exception as e:
            logger.error(f"Failed to get content from Azure Blob Storage: {e}")
            return None
        
    async def get_content_metadata(self, contentUri):
        try:
            blob_client = await self.blob_service.get_blob_client(contentUri)
            properties = await blob_client.get_blob_properties()
            return {
                "name": properties.name,
                "size": properties.size,
                "content_type": properties.content_type,
                "last_modified": properties.last_modified
            }
        except Exception as e:
            logger.error(f"Failed to get content metadata from Azure Blob Storage: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test the connection to Azure Blob Storage."""
        try:
            await self.blob_service.test_connection()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Azure Blob Storage: {e}")
            return False