from typing import List
import logging
import base64


from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig

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
            import json
            return json.loads(mappings_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing index field mappings: {e}")
            raise ValueError("Invalid index field mappings format.")

    
    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:

        # Check if input_data has the required data structure
        if not input_data or not isinstance(input_data, StepInputOutput) or not hasattr(input_data, 'data') or input_data.data is None:
            logger.error(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
            raise StepExecutionError(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
        
        # get documents from input data
        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            raise ValueError(f"No documents list found in input data.")

        # get Azure AI Search Service from context
        ai_search_service = self.get_ai_search_service(context)
        if not ai_search_service:
            logger.error("Azure AI Search Service not found in context.")
            raise StepExecutionError("Azure AI Search Service not found in context.")

        _stats = {
            "total_documents": len(documents),
            "successful_documents": 0,
            "failed_documents": 0,
        }

        # Iterate through each document in the input data
        logger.info(f"Processing {len(documents)} documents...")
            
        for document in documents:
            try:
                if self.debug_mode:
                    logger.debug(f"Processing document: {document}")
                
                # Check if the document is a dictionary
                if not isinstance(document, dict):
                    raise ValueError(f"Invalid document format: {document}. Expected a dictionary.")
                    
                # Process each document
                # This will extend the document with extracted text and images for each page/chunk
                await self.process_document(document=document, 
                                            context=context, 
                                            ai_search_service=ai_search_service)

                _stats["successful_documents"] += 1

                if self.debug_mode:
                    logger.debug(f"Successfully processed document: {document}")

            except Exception as e:
                logger.error(f"Error processing document {document}: {e}")
                _stats["failed_documents"] += 1

                if self.fail_step_on_document_error:
                    # If the step is configured to fail on document error, raise an exception
                    raise StepExecutionError(f"Failed to process document {document}: {e}")

        # Return the updated StepInputOutput
        return StepInputOutput(summary_data=
                                    {
                                        **input_data.summary_data, f"{self.name}_stats": _stats
                                    }, 
                               data=
                                    {
                                        **input_data.data
                                    })


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
            # get the chunks from the document
            chunks = document.get("chunks", None)

            if not chunks:
                logger.error(f"No chunks found in document: {document}.")
                raise StepExecutionError(f"No chunks found in document: {document}. Please check the document structure and try again.")

            # generate the documents to be indexed
            index_documents = []

            for chunk in chunks:
                index_doc = {}
                for doc_field, index_field in self.index_field_mappings.items():
                    index_doc[index_field] = value = chunk.get(doc_field, None)

                index_documents.append(index_doc)


            # Write documents to Azure AI Search Index
            logger.debug(f"Writing {len(index_documents)} documents to Azure AI Search Index '{self.index_name}'")
            indexing_result = await ai_search_service.write_documents(index_name=self.index_name, documents=index_documents)

            if self.debug_mode:
                logger.debug(f"Indexing result: {indexing_result}")

            logger.debug(f"Successfully wrote {len(index_documents)} documents to Azure AI Search Index '{self.index_name}'")

        except Exception as e:
            logger.error(f"Error writing to Azure AI Search Index: {e}")
            raise StepExecutionError(f"Error writing to Azure AI Search Index: {e}")


    def convert_png_to_base64(self, png_path: str) -> str:
        """
        Convert a PNG file to a base64 encoded string.
        
        :param png_path: Path to the PNG file.
        :return: Base64 encoded string of the PNG file.
        """
        with open(png_path, "rb") as png_file:
            png_data = png_file.read()
            return base64.b64encode(png_data).decode('ascii')