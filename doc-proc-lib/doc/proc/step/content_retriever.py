import logging
import tempfile
import os
from pathlib import Path

import aiohttp


from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.source.source_base import SourceItem, SourceBase
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.content_retriever")


class ContentRetrieverStep(StepBase):
    """
    Step to retrieve and download content from sources.
    
    Configuration:
    - 
    """

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Extract configuration settings
        self.include_content_bytes_as_field = self.settings.get("include_content_bytes_as_field", False)
        self.use_temp_file_for_content = self.settings.get("use_temp_file_for_content", True)
        self.temp_folder = self.settings.get("temp_folder", "./tmp/docproc_downloads")

        # If temp_folder is specified, ensure it exists
        if self.temp_folder:
            os.makedirs(self.temp_folder, exist_ok=True)
        
        logger.debug(f"Initialized ContentRetrieverStep with temp_folder: {self.temp_folder}")

    async def run(self, document: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        """
        Retrieve content for the given document from the source.
        
        Args:
            document: Input document to process
            context: Pipeline execution context
            
        Returns:
            Document: Output with content retrieved.
        """

        # Check if document has the required data structure
        if not document or not isinstance(document, Document) or document.id is None:
            logger.error(f"Invalid input document: {document}. Expected Document instance with 'id' attribute.")
            raise StepExecutionError(f"Invalid input document: {document}. Expected Document instance.")

        # get document from input data
        doc_identifier = document.id
        if not doc_identifier.canonical_id or not doc_identifier.source_name:
            logger.error(f"Document identifier is missing required fields (canonical_id, source_name).")
            raise StepExecutionError(f"Documnent identifier is missing required fields (canonical_id, source_name).")

        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {doc_identifier.canonical_id} from source: {doc_identifier.source_name}")

            processed_doc = await self._process_document(doc_identifier, context)

            logger.debug(f"Successfully processed document: {doc_identifier.canonical_id}")

            # write the content to a temp file if content exists
            if processed_doc.get('content'):
                if self.use_temp_file_for_content:
                    temp_file_path = os.path.join(self.temp_folder, f"{doc_identifier.path.replace('/', '_').replace('\\', '_')}")
                    with open(temp_file_path, 'wb') as temp_file:
                        temp_file.write(processed_doc['content'])
                        
                    logger.debug(f"Content written to temporary file: {temp_file_path}")
                    document.data['temp_file_path'] = temp_file_path
            
            if self.include_content_bytes_as_field:
                document.data['content'] = processed_doc.get('content', None)
            
            document.data['metadata'] = processed_doc.get('metadata', {})
            
            return document

        except Exception as e:
            logger.error(f"Error in Content Retriever Step: {e}")
            raise e

    async def _process_document(self, doc_id: ContentIdentifier, context: "PipelineExecutionContext") -> dict:
        """Process a single document for file download."""
        
        source_name = doc_id.source_name
        
        # manage local sources where content is already available on the local filesystem
        if source_name == "local_file":
            local_path = doc_id.path
            if not os.path.isfile(local_path):
                raise FileNotFoundError(f"Local file '{local_path}' not found for document ID '{doc_id.canonical_id}'.")

            with open(local_path, 'rb') as file:
                content_bytes = file.read()
            
            return {
                "metadata": {
                    "source": "local_file",
                    "path": local_path
                },
                "content": content_bytes
            }
        
        # get the source from context
        source_instance: SourceBase = context.get_source(source_name)
        if not source_instance:
            raise StepExecutionError(f"Source '{source_name}' not found in context sources.")

        source_item: SourceItem = await source_instance.retrieve_item(doc_id)
        if source_item:
            
            return {
                "metadata": source_item.metadata.to_dict() if source_item.metadata else {},
                "content": source_item.content if source_item.content else None,
            }

    