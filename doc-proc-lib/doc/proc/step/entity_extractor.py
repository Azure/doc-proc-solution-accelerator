import base64
import hashlib
import os
import re
import logging
import json
from typing import List, Dict, Set

from azure.ai.inference.models import (
        SystemMessage,
        UserMessage
    )

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.entity_extractor") # need to specify the logger name as this module is loaded dynamically

#TODO: fic this one
class EntityExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Set default values for settings if not provided
        self.chunk_field_to_extract_entities_from = self.settings.get("chunk_field_to_extract_entities_from", "text")
        if not self.chunk_field_to_extract_entities_from:
            logger.error("Chunk field to extract entities from not found in settings.")
            raise ValueError("Chunk field to extract entities from not found in settings.")

        self.output_field_name = self.settings.get("output_field_name", "extracted_entities")
        if not self.output_field_name:
            logger.error("Output field name not found in settings.")
            raise ValueError("Output field name not found in settings.")

        # Configure which entity types to extract
        self.extract_people = self.settings.get("extract_people", True)
        self.extract_places = self.settings.get("extract_places", True)
        self.extract_locations = self.settings.get("extract_locations", True)
        self.extract_organizations = self.settings.get("extract_organizations", True)
        self.extract_relationships = self.settings.get("extract_relationships", True)

        # Custom entity types (optional)
        self.custom_entity_types = self.settings.get("custom_entity_types", [])

        # Output format options
        self.output_format = self.settings.get("output_format", "structured")  # "structured" or "json"
        self.include_confidence = self.settings.get("include_confidence", True)
        self.include_context = self.settings.get("include_context", True)

        # get prompts from settings
        self.prompts = self.settings.get("prompts", {})
        if not self.prompts:
            logger.error("No prompts found in settings.")
            raise StepExecutionError("No prompts found in settings.")

        self.system_prompt = self.prompts.get("system", self._get_default_system_prompt())
        if not self.system_prompt:
            logger.error("System prompt not found in settings.")
            raise StepExecutionError("System prompt not found in settings.")

        self.user_prompt = self.prompts.get("user", self._get_default_user_prompt())
        if not self.user_prompt:
            logger.error("User prompt not found in settings.")
            raise StepExecutionError("User prompt not found in settings.")

        self.max_completion_tokens = self.settings.get("max_completion_tokens", 4000)
        self.temperature = self.settings.get("temperature", 0.1)  # Lower temperature for more consistent extraction
        self.top_p = self.settings.get("top_p", 1.0)
        self.frequency_penalty = self.settings.get("frequency_penalty", 0.0)
        self.presence_penalty = self.settings.get("presence_penalty", 0.0)

        if self.debug_mode:
            logger.debug(f"Initialized EntityExtractorStep with settings: {self.settings}")

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for entity extraction."""
        entity_types = []
        if self.extract_people:
            entity_types.append("PERSON (people, names of individuals)")
        if self.extract_places:
            entity_types.append("PLACE (geographical locations, cities, countries, landmarks)")
        if self.extract_locations:
            entity_types.append("LOCATION (addresses, buildings, facilities)")
        if self.extract_organizations:
            entity_types.append("ORGANIZATION (companies, institutions, agencies)")
        
        entity_types_str = ", ".join(entity_types)
        
        custom_types_str = ""
        if self.custom_entity_types:
            custom_types_str = f", {', '.join(self.custom_entity_types)}"

        relationships_instruction = ""
        if self.extract_relationships:
            relationships_instruction = """
Also extract RELATIONSHIPS between entities, such as:
- Person works for Organization
- Person lives in Location
- Organization located in Place
- Any other meaningful relationships between entities"""

        return f"""You are an expert entity extraction system. Your task is to identify and extract entities from the provided text.

Extract the following entity types: {entity_types_str}{custom_types_str}

{relationships_instruction}

Requirements:
- Be precise and accurate in your extractions
- Only extract entities that are clearly mentioned in the text
- Provide confidence scores (1-10) for each extraction
- Include surrounding context for each entity when possible
- Format the output as valid JSON

Output Format:
{{
    "entities": [
        {{
            "text": "entity text as it appears",
            "type": "ENTITY_TYPE",
            "confidence": confidence_score,
            "context": "surrounding text context",
            "start_position": start_char_position,
            "end_position": end_char_position
        }}
    ],
    "relationships": [
        {{
            "entity1": "first entity",
            "entity2": "second entity", 
            "relationship": "relationship description",
            "confidence": confidence_score,
            "context": "supporting text context"
        }}
    ]
}}"""

    def _get_default_user_prompt(self) -> str:
        """Get default user prompt for entity extraction."""
        return """Please extract entities and relationships from the following text:

{chunk_content}

Return only the JSON output with extracted entities and relationships."""

    async def run(self, input_data: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        """ Run the entity extractor step to process documents and extract entities."""

        # Check if input_data has the required data structure
        if not input_data or not isinstance(input_data, Document) or not hasattr(input_data, 'data') or input_data.data is None:
            logger.error(f"Invalid input data: {input_data}. Expected Document instance.")
            raise StepExecutionError(f"Invalid input data: {input_data}. Expected Document instance.")

        # get Azure AI Model Inference Service from context
        ai_model_inference_service = self.get_ai_inference_service(context)
        if not ai_model_inference_service:
            logger.error("Azure AI Model Inference Service not found in context.")
            raise StepExecutionError("Azure AI Model Inference Service not found in context.")

        _stats = {
            "total_documents": 0,
            "successful_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "total_entities_extracted": 0,
            "total_relationships_extracted": 0,
        }

        # get documents from input data
        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            logger.warning(f"No documents found in input data: {input_data.data}. Expected a list of documents.")
            # do nothing if no documents are found
            return StepInputOutput(summary_data={
                                        **input_data.summary_data, f"{self.name}_stats": _stats
                                   },
                                   data={
                                       **input_data.data
                                   })

        _stats["total_documents"] = len(documents)

        # Iterate through each filtered document in the input data
        logger.info(f"Processing {len(documents)} documents...")

        for document in documents:
            try:
                if self.debug_mode:
                    logger.debug(f"Processing document: {document}")

                # Check if the document is a dictionary
                if not isinstance(document, dict):
                    raise ValueError(f"Invalid document format: {document}. Expected a dictionary with attributes.")
                
                # Evaluate condition if present
                if self.condition:
                    skip_document = self.evaluate_document_condition(document, input_data)
                    if skip_document:
                        _stats["skipped_documents"] += 1
                        logger.debug(f"Document skipped due to condition not met: {self.condition}")
                        continue

                # Process each document
                # This will extend the document with extracted entities for each page/chunk
                doc_stats = await self.process_document(document=document, 
                                                       context=context, 
                                                       ai_model_inference_service=ai_model_inference_service)
                
                _stats["successful_documents"] += 1
                _stats["total_entities_extracted"] += doc_stats.get("entities_extracted", 0)
                _stats["total_relationships_extracted"] += doc_stats.get("relationships_extracted", 0)

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
    
    
    def get_ai_inference_service(self, context: "PipelineExecutionContext"):
        """
        Get the AI Model Inference Service from the context.
        
        :param context: PipelineExecutionContext instance.
        :return: AI Model Inference Service instance.
        """

        for name in self.services:
            cs = context.get_service(name)
            if cs and cs.type == 'azure_ai_inference':
                return cs

        return None
    

    async def process_document(self, document: dict, context: "PipelineExecutionContext", ai_model_inference_service) -> Dict:
        """
        Process a single document to extract entities.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        # get the chunks from the document
        chunks = document.get("chunks", [])
        if not chunks:
            logger.error(f"No chunks found in document: {document}.")
            raise StepExecutionError(f"No chunks found in document: {document}.")

        logger.debug(f"Processing {len(chunks)} chunks.")

        doc_stats = {
            "entities_extracted": 0,
            "relationships_extracted": 0
        }

        # Process each chunk
        for chunk in chunks:
            chunk_stats = await self.process_chunk(chunk=chunk, 
                                                  context=context, 
                                                  ai_model_inference_service=ai_model_inference_service)
            
            doc_stats["entities_extracted"] += chunk_stats.get("entities_extracted", 0)
            doc_stats["relationships_extracted"] += chunk_stats.get("relationships_extracted", 0)

        return doc_stats

            
    async def process_chunk(self, chunk: dict, context: "PipelineExecutionContext", ai_model_inference_service) -> Dict:
        """
        Process a single chunk to extract entities and relationships.
        
        :param chunk: Chunk dictionary containing text and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with extraction statistics.
        """
    
        chunk_stats = {
            "entities_extracted": 0,
            "relationships_extracted": 0
        }

        # Extract entities from the specified chunk field
        if self.chunk_field_to_extract_entities_from in chunk:
            chunk_field_value = chunk[self.chunk_field_to_extract_entities_from]
                    
            if isinstance(chunk_field_value, str) and chunk_field_value.strip():
                # Use the AI Model Inference Service to extract entities
                # Prepare the user message with the chunk content
                if "{chunk_content}" in self.user_prompt:
                    # If the user prompt contains a placeholder for chunk content, format it
                    user_message = self.user_prompt.format(chunk_content=chunk_field_value)
                else:
                    # If no placeholder, use the user prompt as is and append the chunk content
                    user_message = f"{self.user_prompt}\n\n{chunk_field_value}"
                            
                chat_completion_messages = [
                        SystemMessage(content=self.system_prompt),
                        UserMessage(user_message)
                    ]
                            
                response = ai_model_inference_service.run_chat_completion(
                                messages=chat_completion_messages,
                                max_completion_tokens=self.max_completion_tokens,
                                temperature=self.temperature,
                                top_p=self.top_p,
                                frequency_penalty=self.frequency_penalty,
                                presence_penalty=self.presence_penalty
                            )
                            
                ai_response = response.choices[0].message.content

                if self.debug_mode:
                    logger.debug(f"AI response for chunk {chunk.get('chunk_num', 'unknown')}: {ai_response}")
                        
                # Parse and store the extracted entities
                extracted_data = self.parse_extraction_response(ai_response)
                
                if self.output_format == "json":
                    chunk[self.output_field_name] = ai_response
                else:
                    chunk[self.output_field_name] = extracted_data
                
                # Update statistics
                if extracted_data and isinstance(extracted_data, dict):
                    entities = extracted_data.get("entities", [])
                    relationships = extracted_data.get("relationships", [])
                    chunk_stats["entities_extracted"] = len(entities) if entities else 0
                    chunk_stats["relationships_extracted"] = len(relationships) if relationships else 0

            else:
                logger.warning(f"The value of {self.chunk_field_to_extract_entities_from} is not a string or is empty. Skipping this chunk.")
                chunk[self.output_field_name] = {} if self.output_format == "structured" else ""
        else:
            logger.warning(f"Chunk field '{self.chunk_field_to_extract_entities_from}' not found in chunk: {chunk}. Skipping entity extraction for this chunk.")
            chunk[self.output_field_name] = {} if self.output_format == "structured" else ""

        return chunk_stats

    def parse_extraction_response(self, ai_response: str) -> Dict:
        """
        Parse the AI response to extract structured entity data.
        
        :param ai_response: Raw AI response containing extracted entities.
        :return: Parsed entity data as dictionary.
        """
        try:
            # Try to parse as JSON first
            if ai_response.strip().startswith('{'):
                return json.loads(ai_response)
            
            # If not JSON, try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # If still no valid JSON, try to find JSON-like content
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            # If all else fails, return empty structure
            logger.warning(f"Could not parse extraction response as JSON: {ai_response}")
            return {"entities": [], "relationships": []}
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}. Response: {ai_response}")
            return {"entities": [], "relationships": []}
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}. Response: {ai_response}")
            return {"entities": [], "relationships": []}

    def filter_entities_by_type(self, entities: List[Dict]) -> List[Dict]:
        """
        Filter entities based on configured entity types.
        
        :param entities: List of extracted entities.
        :return: Filtered list of entities.
        """
        if not entities:
            return []
        
        allowed_types = set()
        if self.extract_people:
            allowed_types.add("PERSON")
        if self.extract_places:
            allowed_types.add("PLACE")
        if self.extract_locations:
            allowed_types.add("LOCATION")
        if self.extract_organizations:
            allowed_types.add("ORGANIZATION")
        
        # Add custom entity types
        allowed_types.update(self.custom_entity_types)
        
        # Filter entities
        filtered_entities = []
        for entity in entities:
            entity_type = entity.get("type", "").upper()
            if entity_type in allowed_types:
                filtered_entities.append(entity)
        
        return filtered_entities

    def deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Remove duplicate entities based on text and type.
        
        :param entities: List of entities to deduplicate.
        :return: Deduplicated list of entities.
        """
        if not entities:
            return []
        
        seen = set()
        deduplicated = []
        
        for entity in entities:
            entity_key = (entity.get("text", "").lower(), entity.get("type", "").upper())
            if entity_key not in seen:
                seen.add(entity_key)
                deduplicated.append(entity)
        
        return deduplicated

    def enhance_entities_with_metadata(self, entities: List[Dict], chunk: Dict) -> List[Dict]:
        """
        Enhance entities with additional metadata from the chunk.
        
        :param entities: List of entities to enhance.
        :param chunk: Source chunk containing metadata.
        :return: Enhanced entities with metadata.
        """
        if not entities:
            return []
        
        enhanced_entities = []
        for entity in entities:
            enhanced_entity = entity.copy()
            
            # Add chunk metadata
            enhanced_entity["source_chunk_id"] = chunk.get("chunk_id")
            enhanced_entity["source_chunk_num"] = chunk.get("chunk_num")
            enhanced_entity["source_file"] = chunk.get("input_file_path")
            
            # Add page number if available
            if "page_num" in chunk:
                enhanced_entity["page_num"] = chunk["page_num"]
            
            enhanced_entities.append(enhanced_entity)
        
        return enhanced_entities
