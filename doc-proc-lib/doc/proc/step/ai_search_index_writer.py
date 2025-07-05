from typing import List
import logging
import base64


from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput

logger = logging.getLogger("doc.proc.step.ai_search_index_writer")

class AISearchIndexWriterStep(StepBase):
    """
    Step to write to Azure AI Search Index.
    
    """

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, fail_step_on_document_error: bool = False, debug_mode: bool = False, services: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, fail_step_on_document_error=fail_step_on_document_error, debug_mode=debug_mode, services=services, settings=settings, **kwargs)

        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # get search index name from settings
        self.index_name = self.settings.get("index_name", "")
        if not self.index_name:
            logger.error("Index name not found in settings.")
            raise ValueError("Index name not found in settings.")

        # get chunks data iterator field from settings
        self.chunks_iterator_field = self.settings.get("chunks_iterator_field", "")
        if not self.chunks_iterator_field:
            logger.error("Chunks iterator field not found in settings.")
            raise ValueError("Chunks iterator field not found in settings.")

        self.index_field_mappings = self.settings.get("index_field_mappings", "")
        if not self.index_field_mappings:
            logger.error("Index field mappings not found in settings.")
            raise ValueError("Index field mappings not found in settings.")
        
        self.index_field_mappings = self.parse_index_field_mappings(self.index_field_mappings)

        logger.debug(f"Initialized AISearchIndexWriterStep with index_name: {self.index_name}, "
                     f"chunks_iterator_field: {self.chunks_iterator_field}, "
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


    def convert_png_to_base64(self, png_path: str) -> str:
        """
        Convert a PNG file to a base64 encoded string.
        
        :param png_path: Path to the PNG file.
        :return: Base64 encoded string of the PNG file.
        """
        with open(png_path, "rb") as png_file:
            png_data = png_file.read()
            return base64.b64encode(png_data).decode('ascii')
        
    
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


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:

        # get Azure AI Search Service from context
        ai_search_service = self.get_ai_search_service(context)
        if not ai_search_service:
            logger.error("Azure AI Search Service not found in context.")
            raise StepExecutionError("Azure AI Search Service not found in context.")

        # Get the chunks data from input

        try:
            # get the chunks data from input
            chunks_iterator_field_parts = self.chunks_iterator_field.split(".")
            if chunks_iterator_field_parts[0] == "":
                logger.error("Chunks iterator field is empty.")
                raise StepExecutionError("Chunks iterator field is empty.")
            
            chunks_data = None
            if chunks_iterator_field_parts[0] == "data":
                chunks_data = input_data.data

                for part in chunks_iterator_field_parts[1:]:
                    chunks_data = chunks_data.get(part, {})
            
            if not chunks_data:
                logger.error(f"No chunks data found in input based on chunks_iterator_field: {self.chunks_iterator_field}. Check the field path.")
                raise StepExecutionError(f"No chunks data found in input based on chunks_iterator_field: {self.chunks_iterator_field}. Check the field path.")

            # generate the documents to be indexed
            documents = []
            for chunk in chunks_data:
                document = {}
                for doc_field, index_field in self.index_field_mappings.items():
                    # Handle nested fields
                    field_parts = doc_field.split(".")
                    value = chunk
                    for part in field_parts:
                        value = value.get(part, None)
                        if value is None:
                            break
                    
                    if value is not None:
                        document[index_field] = value
                
                documents.append(document)

                if self.debug_mode:
                    logger.debug(f"Processed document for indexing: {document}")
                
            # Write documents to Azure AI Search Index
            logger.debug(f"Writing {len(documents)} documents to Azure AI Search Index '{self.index_name}'")
            indexing_result = await ai_search_service.write_documents(index_name=self.index_name, documents=documents)

            if self.debug_mode:
                logger.debug(f"Indexing result: {indexing_result}")
            
            logger.debug(f"Successfully wrote {len(documents)} documents to Azure AI Search Index '{self.index_name}'")

        except Exception as e:
            logger.error(f"Error writing to Azure AI Search Index: {e}")
            raise StepExecutionError(f"Error writing to Azure AI Search Index: {e}")


        # Return the updated StepInputOutput
        return StepInputOutput(summary_data=
                                            {
                                                **input_data.summary_data
                                            },
                               data=        {
                                                **input_data.data,
                                                "chunks_data": chunks_data
                                            })