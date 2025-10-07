import logging
import tempfile
import os
from pathlib import Path

import aiohttp

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.file_downloader")


class FileDownloaderStep(StepBase):
    """
    Step to download files from Azure Blob Storage or SAS URLs to a local temporary directory.
    
    This step processes documents that have blob_details or blob_sas_url fields and downloads
    the files to a configurable temporary directory. It adds the local file_path to the document.
    
    Configuration:
    - temp_folder: Path to temporary folder (optional, uses system temp if not specified)
    """

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Extract configuration settings
        self.temp_folder = self.settings.get("temp_folder", "./tmp/docproc_downloads")

        # If temp_folder is specified, ensure it exists
        if self.temp_folder:
            os.makedirs(self.temp_folder, exist_ok=True)

        logger.debug(f"Initialized FileDownloaderStep with temp_folder: {self.temp_folder}")

    async def run(self, document: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        """
        Download files for documents that have blob storage references.
        
        Args:
            document: Input document to process
            context: Pipeline execution context
            
        Returns:
            Document: Output with local file_path added to documents that were downloaded
        """

        # Check if document has the required data structure
        if not document or not isinstance(document, Document) or not hasattr(document, 'data') or document.data is None:
            logger.error(f"Invalid input document: {document}. Expected Document instance with 'data' attribute.")
            raise StepExecutionError(f"Invalid input document: {document}. Expected Document instance.")

        # get document from input data
        doc_to_process = document.data
        if not doc_to_process or not isinstance(doc_to_process, dict):
            logger.error(f"No document data found in input data: {document.data}. Expected a dictionary of fields.")
            raise StepExecutionError(f"No document data found in input data: {document.data}. Expected a dictionary of fields.")

        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {doc_to_process}")

            processed_doc = await self._process_document(doc_to_process, context)

            logger.debug(f"Successfully processed document: {document.id}")

            return Document(summary_data={**document.summary_data}, data=processed_doc)

        except Exception as e:
            logger.error(f"Error in FileDownloaderStep: {e}")
            raise e

    async def _process_document(self, doc: dict, context: "PipelineExecutionContext") -> dict:
        """Process a single document for file download."""
        
        # Check if document already has a local file_path and skip download
        if "file_path" in doc and doc["file_path"]:
            logger.debug(f"Document already has local file_path: {doc['file_path']}")
            return doc

        # Check what download method to use
        if "blob_details" in doc:
            blob_service = self._get_blob_service(context)
            if not blob_service:
                logger.warning("blob_details found but no Azure Blob Storage service available")
                return doc
            
            temp_file_path = await self._download_blob_from_details(doc["blob_details"], blob_service)
            doc["file_path"] = temp_file_path
            logger.debug(f"Downloaded blob to: {temp_file_path}")
            
        elif "blob_sas_url" in doc:
            temp_file_path = await self._download_blob_from_sas_url(doc["blob_sas_url"])
            doc["file_path"] = temp_file_path
            logger.debug(f"Downloaded blob from SAS URL to: {temp_file_path}")
            
        else:
            logger.debug("No downloadable blob reference found in document")

        return doc

    def _get_blob_service(self, context: "PipelineExecutionContext"):
        """
        Get the Azure Blob Service from the context.

        :param context: PipelineExecutionContext instance.
        :return: Azure Blob Service instance.
        """
        for name in self.services:
            cs = context.get_service(name)
            if cs and cs.type == 'azure_blob_storage':
                return cs

        return None

    async def _download_blob_from_details(self, blob_details: dict, blob_service) -> str:
        """
        Download blob content from Azure Storage using blob details and save to temporary file.
        
        Args:
            blob_details: Dictionary containing container and blob information
                         Expected format: {"container": "container_name", "blob": "blob_name"}
            blob_service: The Azure Blob Storage service instance
            
        Returns:
            str: Path to the temporary file containing the downloaded content
            
        Raises:
            StepExecutionError: If download fails or blob details are invalid
        """
        if not blob_details or not isinstance(blob_details, dict):
            raise StepExecutionError("Invalid blob details provided. Expected a dictionary.")
        
        container_name = blob_details.get("container")
        blob_name = blob_details.get("blob")
        
        if not container_name or not isinstance(container_name, str):
            raise StepExecutionError("Missing or invalid 'container' in blob details")
            
        if not blob_name or not isinstance(blob_name, str):
            raise StepExecutionError("Missing or invalid 'blob' in blob details")
            
        if not blob_service:
            raise StepExecutionError("Blob service is required but not provided")
            
        logger.debug(f"Downloading blob '{blob_name}' from container '{container_name}'...")
        
        try:
            # Create a temporary file to store the downloaded content
            # Use configured temp folder
            os.makedirs(self.temp_folder, exist_ok=True)
            temp_file_path = os.path.join(self.temp_folder, blob_name.replace('/', '_'))

            # Use the blob service to download the file
            async with blob_service:
                await blob_service.download_file(
                    container_name=container_name,
                    filename=blob_name, 
                    download_path=temp_file_path
                )
            
            logger.debug(f"Successfully downloaded blob to temporary file: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            # Clean up the temporary file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise StepExecutionError(f"Failed to download blob: {str(e)}")

    async def _download_blob_from_sas_url(self, sas_url: str) -> str:
        """
        Download blob content from Azure Storage using SAS URL and save to temporary file.
        
        Args:
            sas_url: The SAS URL to download the blob from
            
        Returns:
            str: Path to the temporary file containing the downloaded content
            
        Raises:
            StepExecutionError: If download fails or SAS URL is invalid
        """
        if not sas_url or not isinstance(sas_url, str):
            raise StepExecutionError("Invalid SAS URL provided")
            
        logger.debug(f"Downloading blob from SAS URL: {sas_url[:50]}...")
        
        try:
            # Create a temporary file to store the downloaded content
            os.makedirs(self.temp_folder, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(delete=False, dir=self.temp_folder)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Download the blob using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(sas_url) as response:
                    # Check if the request was successful
                    if response.status != 200:
                        # Clean up the temporary file
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                        raise StepExecutionError(
                            f"Failed to download blob. HTTP status: {response.status}, "
                            f"reason: {response.reason}"
                        )
                    
                    # Read the content and write to temporary file
                    with open(temp_file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            logger.debug(f"Successfully downloaded blob to temporary file: {temp_file_path}")
            return temp_file_path
            
        except aiohttp.ClientError as e:
            # Clean up the temporary file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise StepExecutionError(f"HTTP client error while downloading blob: {str(e)}")
            
        except Exception as e:
            # Clean up the temporary file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise StepExecutionError(f"Unexpected error while downloading blob: {str(e)}")
