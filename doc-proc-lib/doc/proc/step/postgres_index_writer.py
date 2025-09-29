import logging

import json

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

from psycopg2.extensions import register_adapter, AsIs

logger = logging.getLogger("doc.proc.step.postgres_index_writer")

class PostgresIndexWriterStep(StepBase):
    """
    Step to write to PostgreSQL database.
    """

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)

        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # get search index name from settings
        self.database = self._parse_env(self.settings.get("database", ""))

        self.index_field_mappings = self.settings.get("index_field_mappings", "")
        if not self.index_field_mappings:
            logger.error("Index field mappings not found in settings.")
            raise ValueError("Index field mappings not found in settings.")
        
        self.index_field_mappings = self.parse_index_field_mappings(self.index_field_mappings)

        logger.debug(f"Initialized PostgresIndexWriterStep with database: {self.database}, "
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

    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
      
        # get PostgreSQL Service from context
        postgres_service = self.get_postgres_service(context)
        if not postgres_service:
            logger.error("PostgreSQL Service not found in context.")
            raise StepExecutionError("PostgreSQL Service not found in context.")

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
                                        postgres_service=postgres_service)


            if self.debug_mode:
                logger.debug(f"Successfully processed document: {document}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")

            if self.fail_step_on_document_error:
                # If the step is configured to fail on document error, raise an exception
                raise StepExecutionError(f"Failed to process document: {e}")

        # Return the updated StepInputOutput
        return input_data

    def get_postgres_service(self, context: "PipelineExecutionContext"):
        """
        Get the PostgreSQL Service from the context.

        This method searches for a service of type 'postgres' in the provided context.
        :param context: PipelineExecutionContext instance.
        :return: PostgreSQL Service instance.
        """

        for name in self.services:
            cs = context.get_service(name)
            
            if cs and cs.type == 'azure_postgres':
                return cs

        return None


    async def process_document(self, document: dict, context: "PipelineExecutionContext", postgres_service) -> None:
        """Process a single document and write it to the PostgreSQL database.

        Args:
            document (dict): The document to process.
            context (PipelineExecutionContext): The pipeline execution context.
            postgres_service: The PostgreSQL Service instance.
        """

        try:
            # get the chunks from the document
            chunks = document.get("chunks", None)

            if not chunks:
                logger.error(f"No chunks found in document.")
                raise StepExecutionError(f"No chunks found in document. Please check the document structure and try again.")

            # generate the documents to be indexed
            index_documents = []

            #clear the content (use the chunk text)
            document['content'] = None

            for chunk in chunks:
                index_doc = {}
                
                for doc_field, index_field in self.index_field_mappings.items():
                    value = index_doc.get(index_field, None)

                    if ( value == None):
                        value = chunk.get(doc_field, None)
                    
                    if ( value == None):
                        value = document.get(doc_field, None)

                    if ( value == None and 'metadata' in document):
                        value = document['metadata'].get(doc_field, None)

                    if ( value == None and 'metadata_security' in document):
                        value = document['metadata_security'].get(doc_field, None)

                    if value is not None:
                        index_doc[index_field] = value

                metadata = document.get("metadata", {})
                index_doc['id'] = document.get('id', None)
                index_doc['chunk_id'] = chunk.get('chunk_num', None)
                index_doc['page_id'] = chunk.get('page_num', None)
                index_doc["parent_id"] = document.get("parent_id", None)
                index_doc['entity_ids'] = metadata.get('entity_ids', [])
                index_doc['relationship_ids'] = metadata.get('relationship_ids', [])
                index_doc['document_ids'] = metadata.get('document_ids', [])

                index_doc['content'] = index_doc['content']
                index_documents.append(index_doc)


            # Write documents to PostgreSQL database
            logger.debug(f"Writing {len(index_documents)} documents to PostgreSQL database")
            indexing_result = await postgres_service.write_documents(self.database, documents=index_documents)

            if self.debug_mode:
                logger.debug(f"Indexing result: {indexing_result}")

            logger.debug(f"Successfully wrote {len(index_documents)} documents to PostgreSQL database")

        except Exception as e:
            logger.error(f"Error writing to PostgreSQL database: {e}")
            raise StepExecutionError(f"Error writing to PostgreSQL database: {e}")
        