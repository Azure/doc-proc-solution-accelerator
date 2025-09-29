import logging
import base64
import json

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

logger = logging.getLogger("doc.proc.step.ai_search_index_writer")

class AISearchPurgeStep(StepBase):
    """
    Step to purge item from Azure AI Search Index.
    
    """

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)

        # get search index name from settings
        self.index_name = self.settings.get("index_name", "")
        if not self.index_name:
            logger.error("Index name not found in settings.")
            raise ValueError("Index name not found in settings.")

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
            return json.loads(mappings_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing index field mappings: {e}")
            raise ValueError("Invalid index field mappings format.")

    
    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState, **kwargs) -> StepInputOutput:

        # Check if input_data has the required data structure
        if not input_data or not isinstance(input_data, StepInputOutput) or not hasattr(input_data, 'data') or input_data.data is None:
            logger.error(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
            raise StepExecutionError(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
        

        # get Azure AI Search Service from context
        ai_search_service = self.get_ai_search_service(context)
        if not ai_search_service:
            logger.error("Azure AI Search Service not found in context.")
            raise StepExecutionError("Azure AI Search Service not found in context.")

        # get documents from input data
        document = input_data.data.get("document", {})
        
        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {document}")
            
            # Check if the document is a dictionary
            if not isinstance(document, dict):
                raise ValueError(f"Invalid document format: {document}. Expected a dictionary.")
                
            # Process each document
            await self.process_document(document=document, 
                                        context=context, 
                                        ai_search_service=ai_search_service)


            if self.debug_mode:
                logger.debug(f"Successfully processed document: {document}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")

            if self.fail_step_on_document_error:
                # If the step is configured to fail on document error, raise an exception
                raise StepExecutionError(f"Failed to process document: {e}")

        # Return the updated StepInputOutput
        return StepInputOutput(summary_data={}, 
                               data={
                                        **input_data.data
                                    },
                                remove_state=True)


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


    async def process_document(self, document: dict, context: "PipelineExecutionContext", ai_search_service) -> None:
        """Process a single document and write it to the Azure AI Search Index.

        Args:
            document (dict): The document to process.
            context (PipelineExecutionContext): The pipeline execution context.
            ai_search_service: The Azure AI Search Service instance.
        """

        try:
            items = await ai_search_service.search_documents(self.index_name, select_fields=['id'], filter_field = 'parent_id', filter_value=document['parent_id'], top=1000)

            ids = []
            for document in items['documents']:
                ids.append(document['id'])

            # Write documents to Azure AI Search Index
            logger.debug(f"Purging {len(items)} documents to Azure AI Search Index '{self.index_name}'")
            
            indexing_result = await ai_search_service.delete_documents(index_name=self.index_name, key_field=['id'], key_values=ids)

            if self.debug_mode:
                logger.debug(f"Indexing result: {indexing_result}")

            logger.debug(f"Successfully purged {len(items)} documents to Azure AI Search Index '{self.index_name}'")

        except Exception as e:
            logger.error(f"Error writing to Azure AI Search Index: {e}")
            raise StepExecutionError(f"Error writing to Azure AI Search Index: {e}")