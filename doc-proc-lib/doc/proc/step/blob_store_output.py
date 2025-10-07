import json
import logging
import tempfile
import os
from pathlib import Path

import aiohttp

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.blob_store_output")


class BlobStoreOutputStep(StepBase):
    """
    Step to output the data of the document to a blob store.

    This step processes documents and saves the document as a json file on Azure Blob Storage.

    Configuration:
    - temp_folder: Path to temporary folder (optional, uses system temp if not specified)
    """

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Extract configuration settings
        self.blob_container = self.settings.get("blob_container", "output")
        self.blob_path = self.settings.get("blob_path", "{pipeline_name}/{file_name}")
        self.overwrite = self.settings.get("overwrite", False)
        
        if not self.blob_container or not isinstance(self.blob_container, str):
            logger.error("Invalid or missing 'blob_container' in settings.")
            raise ValueError("Invalid or missing 'blob_container' in settings.")

        if not self.blob_path or not isinstance(self.blob_path, str):
            logger.error("Invalid or missing 'blob_path' in settings.")
            raise ValueError("Invalid or missing 'blob_path' in settings.")

        logger.debug(f"Initialized BlobStoreOutputStep with blob_container: {self.blob_container}, blob_path: {self.blob_path}")

    async def run(self, document: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        """
        Upload the output document to Azure Blob Storage.
        
        Args:
            document: Input document to process
            context: Pipeline execution context

        Returns:
            Document: Output with updated document metadata
        """

        # Check if document has the required data structure
        if not document or not isinstance(document, Document) or not hasattr(document, 'data') or document.data is None:
            logger.error(f"Invalid input document: {document}. Expected Document instance with 'data' attribute.")
            raise StepExecutionError(f"Invalid input document: {document}. Expected Document instance.")

        # get document from input data
        doc_data = document.data
        if not doc_data or not isinstance(doc_data, dict):
            logger.error(f"No document data found in input data: {document.data}. Expected a dictionary of fields.")
            raise StepExecutionError(f"No document data found in input data: {document.data}. Expected a dictionary of fields.")

        doc_id = doc_data.get("id", "unknown")
        
        try:
            logger.debug(f"Processing document: {doc_id}")

            processed_doc = await self._process_document(document, context)

            logger.debug(f"BlobStoreOutputStep completed processing. Document: {doc_id}")

            # Return the processed document, as this will be an instance of Document
            return processed_doc

        except Exception as e:
            logger.error(f"Error in BlobStoreOutputStep: {e}")
            raise e

    async def _process_document(self, doc: Document, context: "PipelineExecutionContext") -> dict:
        """Process a single document for blob storage."""
        
        # get Azure Blob Storage Service from context
        blob_service = self._get_blob_service(context)
        if not blob_service:
            logger.error("Azure Blob Storage Service not found in context.")
            raise StepExecutionError("Azure Blob Storage Service not found in context.")

        file_name = f"{doc.data.get('id', 'unknown_id')}.json"

        pipeline_name = context.pipeline.name if context and context.pipeline and context.pipeline.name else "unknown_pipeline"

        # Prepare blob path and name
        blob_path = f'{pipeline_name}/{file_name}' # default path
        
        if '{pipeline_name}' in self.blob_path and '{file_name}' in self.blob_path:
            blob_path = self.blob_path.format(pipeline_name=pipeline_name, file_name=file_name)
        elif '{pipeline_name}' in self.blob_path:
            blob_path = self.blob_path.format(pipeline_name=pipeline_name)
        elif '{file_name}' in self.blob_path:
            blob_path = self.blob_path.format(file_name=file_name)
        
        logger.debug(f"Uploading file to container '{self.blob_container}' at path '{blob_path}'...")
        
        upload_result = ''
        
        # Use the blob service to upload the file
        async with blob_service:
            upload_result = await blob_service.upload_file(
                                        container_name=self.blob_container,
                                        filename=blob_path,
                                        file_content=doc.model_dump_json(indent=2).encode('utf-8'),
                                        overwrite=self.overwrite
                                    )

        logger.debug(f"Uploaded document to: {upload_result}")

        doc.summary_data['result_blob_url'] = upload_result
        
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
