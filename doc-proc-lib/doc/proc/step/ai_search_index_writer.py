import logging
import base64


from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.ai_search_index_writer")

class AISearchIndexWriterStep(StepBase):
    """
    Step to write to Azure AI Search Index.
    
    """
    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)

        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.chunks_field_name = self.settings.get("chunks_field_name", "chunks")
        if not self.chunks_field_name or self.chunks_field_name.strip() == "":
            logger.error("Chunks field name not found in settings.")
            raise ValueError("Chunks field name not found in settings.")
        self.chunks_field_name = self.chunks_field_name.strip()

        # get search index name from settings
        self.index_name = self.settings.get("index_name", "")
        if not self.index_name:
            logger.error("Index name not found in settings.")
            raise ValueError("Index name not found in settings.")
        self.index_name = self.index_name.strip()
        
        self.index_field_mappings = self.settings.get("index_field_mappings", "")
        if not self.index_field_mappings:
            logger.error("Index field mappings not found in settings.")
            raise ValueError("Index field mappings not found in settings.")
        
        self.index_field_mappings = self.parse_index_field_mappings(self.index_field_mappings)

        logger.debug(f"Initialized AISearchIndexWriterStep with index_name: {self.index_name}, "
                     f"index_field_mappings: {self.index_field_mappings}")

    def parse_index_field_mappings(self, mappings_str: str) -> dict:
        """
        Parse the index field mappings from a string to a dictionary.
        
        :param mappings_str: String representation of the mappings.
        :return: Dictionary of field mappings.
        """
        try:
            # Assuming the mappings are in JSON format
            import json
            return json.loads(mappings_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing index field mappings: {e}")
            raise ValueError("Invalid index field mappings format.")

    async def run(self, document: Document, context: "PipelineExecutionContext", **kwargs) -> Document:

        # Check if document has the required data structure
        if not document or not isinstance(document, Document) or not hasattr(document, 'data') or document.data is None:
            logger.error(f"Invalid input document. Expected Document instance with 'data' attribute.")
            raise StepExecutionError(f"Invalid input document. Expected Document instance.")

        doc_id = document.id

        # get Azure AI Search Service from context
        ai_search_service = self.get_ai_search_service(context)
        if not ai_search_service:
            logger.error("Azure AI Search Service not found in context.")
            raise StepExecutionError("Azure AI Search Service not found in context.")

        # get document from input data
        data_to_process = document.data
        if not data_to_process or not isinstance(data_to_process, dict):
            logger.error(f"No document data found in input data. Expected a dictionary of fields. Reference document id: {doc_id}")
            raise StepExecutionError(f"No document data found in input data. Expected a dictionary of fields. Reference document id: {doc_id}")
            
        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {doc_id}")

            # Process the document
            # This will extend the document with extracted text and images for each page/chunk
            await self._process_document(data=data_to_process, 
                                         context=context, 
                                         ai_search_service=ai_search_service)
                
            logger.debug(f"Successfully processed document: {doc_id}")
                
            # Return the updated document
            return document

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise e

    def get_ai_search_service(self, context: "PipelineExecutionContext"):
        """
        Get the AI Search Service from the context.

        This method searches for a service of type 'azure_ai_search' in the provided context.
        :param context: PipelineExecutionContext instance.
        :return: AI Search Service instance.
        """

        for name in self.services:
            cs = context.get_service(name)
            
            if cs and cs.type == 'azure_ai_search':
                return cs

        return None

    async def _process_document(self, data: dict, context: "PipelineExecutionContext", ai_search_service):
        """Process the document data and write it to the Azure AI Search Index.

        Args:
            data (dict): The document data to process.
            context (PipelineExecutionContext): The pipeline execution context.
            ai_search_service: The Azure AI Search Service instance.
        """
        try:
            # get the chunks from the document
            chunks = data.get(self.chunks_field_name, None)

            if not chunks:
                logger.warning(f"No chunks found in document.")
                return

            # generate the documents to be indexed
            documents_to_index = []

            for chunk in chunks:
                index_doc = {}
                for doc_field, index_field in self.index_field_mappings.items():
                    index_doc[index_field] = chunk.get(doc_field, None)

                documents_to_index.append(index_doc)

            # Write documents to Azure AI Search Index
            logger.debug(f"Writing {len(documents_to_index)} documents to Azure AI Search Index '{self.index_name}'")
            indexing_result = await ai_search_service.write_documents(index_name=self.index_name, documents=documents_to_index)

            if self.debug_mode:
                logger.debug(f"Indexing result: {indexing_result}")

            logger.debug(f"Successfully wrote {len(documents_to_index)} documents to Azure AI Search Index '{self.index_name}'")

        except Exception as e:
            logger.error(f"Error writing to Azure AI Search Index: {e}")
            raise StepExecutionError(f"Error writing to Azure AI Search Index: {e}")
