import logging

from .source_base import SourceBase

from typing import Optional, List, Dict, Any, Iterator, Tuple

from doc.proc.service import ServiceBase, ServiceExecutionError, BlobService, AsyncBlobService
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

from dependencies import get_config

logger = logging.getLogger("doc.proc.source.blob") # need to specify the logger name as this module is loaded dynamically

class BlobSource(SourceBase):
    """Data source for loading data from Azure Blob Storage."""
    def __init__(self, id, name, type, settings: dict):
        super().__init__(id, name, type, settings)

        self.container_name = settings.get("container_name")
        self.file_types = settings.get("file_types", [])
        self.paths = settings.get("paths")
        self.include_metadata = settings.get("include_metadata", False)
        self.recursive = settings.get("recursive", False)
        self.config = get_config()
        self.storage_account_name = self.replace_config_value(settings.get('account_name'))
        self.account_url = f"https://{self.storage_account_name}.blob.core.windows.net"

        self.blob_service = BlobService(
            name="BlobService",
            type="blob_service",
            settings=settings
        )

        self.async_blob_service = AsyncBlobService(
            name="BlobService",
            type="blob_service",
            settings=settings
        )

    async def create_item(self, blob):
        id = f"{self.id}::{self.container_name}::{blob.name}"
        id_hash = self.generate_sha1_hash(id)
        file_path = f"{self.account_url}/{self.container_name}/{blob.name}" 
                
        item = {
            "id": id_hash,
            "url": file_path,
            "parent_id": id,
            "source_name": self.name,
            "source_type": self.type,
            "name": blob.name,
            "size": blob.size,
            "modified": str(blob.last_modified),
            "created": str(blob.creation_time),
            "content_uri": id,
            "file_path": file_path,
            "metadata" : {}
        }
        
        return item

    async def load_data(self) -> StepInputOutput:
        """Load data from Azure Blob Storage."""
        input_output = StepInputOutput()
        input_output.id = self.container_name
        input_output.summary_data = {}
        input_output.data = {}
        input_output.data["documents"] = []

        # Implement data loading logic from Azure Blob Storage here
        await self.async_blob_service._connect()
        container_client = await self.async_blob_service.get_container_client(self.container_name)
        
        # Process each blob
        async for blob in container_client.list_blobs():

            #check if blob has file type
            if not self.file_types or any(blob.name.endswith(ext) for ext in self.file_types):

                item = await self.create_item(blob)
                input_output.data["documents"].append(item)

        return input_output
    
    async def get_document(self, content_identifier : ContentIdentifier):
        await self.async_blob_service._connect()

        vals = content_identifier.canonical_id.split('::')
        container_name = vals[1]
        blob_name = '/'.join(vals[2:])
        container_client = await self.async_blob_service.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        blob = await blob_client.get_blob_properties()

        item = await self.create_item(blob)
        
        return item
    
    async def get_content(self, content_uri):
        """Get the content of a blob from Azure Blob Storage."""
        try:
            vals = content_uri.split('::')
            container_name = vals[1]
            blob_name = '/'.join(vals[2:])
            container_client = await self.async_blob_service.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            content = await blob_client.download_blob()
            return await content.readall()
        except Exception as e:
            logger.error(f"Failed to get content from Azure Blob Storage: {e}")
            return None
        
    async def get_content_metadata(self, content_uri):
        try:
            vals = content_uri.split('::')
            container_name = vals[1]
            blob_name = '/'.join(vals[2:])
            container_client = await self.async_blob_service.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            properties = await blob_client.get_blob_properties()
            item = await self.create_item(properties)
            return item
        except Exception as e:
            logger.error(f"Failed to get content metadata from Azure Blob Storage: {e}")
            return {}

    async def get_content_security(self, content_uri):
        return {
            "metadata_security_id" : []
        }
    
    def get_items(self)->Iterator:
        container_client = self.blob_service.get_container_client(self.container_name)
        
        for blob in container_client.list_blobs():
            id = f"{self.storage_account_name}::{self.container_name}::{blob.name}"
            ci = ContentIdentifier(data_source_object_id=self.name,
                                   canonical_id=f"{self.storage_account_name}::{self.container_name}::{blob.name}",
                                   multipart_id=id.split('::'))
            yield ci

    async def check_changes(self, request: DocProcRequest, state: DocProcState):
        modified = False
        deleted = False
        
        document = await self.get_document(request.content_identifier)

        if (document == None):
            modified = True
            deleted = True
        
        if state.content_identifier.metadata['created'] != str(document.get('created')):
            modified = True
        
        if state.content_identifier.metadata['modified'] != str(document.get('modified')):
            modified = True

        return modified, deleted

    async def check_exists(self, content_identifier : ContentIdentifier):
        pass
    
    async def test_connection(self) -> bool:
        """Test the connection to Azure Blob Storage."""
        try:
            await self.async_blob_service.test_connection()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Azure Blob Storage: {e}")
            return False