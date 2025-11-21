import base64
import hashlib
import os
import re
import logging
from typing import List

from azure.ai.inference.models import (
        SystemMessage,
        UserMessage
    )

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.custom_ai_prompt") # need to specify the logger name as this module is loaded dynamically

class CustomAIPromptStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Set default values for settings if not provided
        self.content_iterator_field = self.settings.get("content_iterator_field", "chunks")
        if not self.content_iterator_field:
            logger.error("Content iterator field not found in settings.")
            raise ValueError("Content iterator field not found in settings.")

        self.chunk_fields_to_apply_prompt_on = self.settings.get("chunk_fields_to_apply_prompt_on", "markdown,text")
        if not self.chunk_fields_to_apply_prompt_on:
            logger.error("Chunk field to apply prompt on not found in settings.")
            raise ValueError("Chunk field to apply prompt on not found in settings.")

        self.output_field_name = self.settings.get("output_field_name", "custom_ai_prompt_output")
        if not self.output_field_name:
            logger.error("Output field name not found in settings.")
            raise ValueError("Output field name not found in settings.")

        # get prompts from settings
        self.system_prompt = self.settings.get("system_prompt", "")
        if not self.system_prompt:
            logger.error("System prompt not found in settings.")
            raise StepExecutionError("System prompt not found in settings.")

        self.user_prompt = self.settings.get("user_prompt", "")
        if not self.user_prompt:
            logger.error("User prompt not found in settings.")
            raise StepExecutionError("User prompt not found in settings.")

        self.max_completion_tokens = self.settings.get("max_completion_tokens", 4000)
        self.temperature = self.settings.get("temperature", 1.0)
        self.top_p = self.settings.get("top_p", 1.0)
        self.frequency_penalty = self.settings.get("frequency_penalty", 0.0)
        self.presence_penalty = self.settings.get("presence_penalty", 0.0)

        if self.debug_mode:
            logger.debug(f"Initialized CustomAIPromptStep with settings: {self.settings}")


    async def run(self, document: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        """
        Run the step processing logic for AI custom prompt enrichment.

        Args:
            document: Input document to analyze
            context: Pipeline execution context

        Returns:
            Document: Output with AI enriched results as per the prompt
        """
        
        # Check if document has the required data structure
        if not document or not isinstance(document, Document) or not hasattr(document, 'data') or document.data is None:
            logger.error(f"Invalid input document. Expected Document instance with 'data' attribute.")
            raise StepExecutionError(f"Invalid input document. Expected Document instance.")

        doc_id = document.id

        # get Azure AI Model Inference Service from context
        ai_model_inference_service = self._get_ai_inference_service(context)
        if not ai_model_inference_service:
            logger.error("Azure AI Model Inference Service not found in context.")
            raise StepExecutionError("Azure AI Model Inference Service not found in context.")

        # get document from input data
        data_to_process = document.data
        if not data_to_process or not isinstance(data_to_process, dict):
            logger.error(f"No document data found in input data. Expected a dictionary of fields. Reference document id: {doc_id}")
            raise StepExecutionError(f"No document data found in input data. Expected a dictionary of fields. Reference document id: {doc_id}")

        
        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {data_to_process}")

            # Validate required fields - now only chunks is required
            if self.content_iterator_field not in data_to_process:
                raise StepExecutionError(f"Invalid document format. Document is missing the required '{self.content_iterator_field}' field.")

            # Process the document
            # This will extend the document with extracted text and images for each page/chunk
            await self._process_document(data=data_to_process, 
                                                       context=context, 
                                                       ai_model_inference_service=ai_model_inference_service)

            logger.debug(f"Successfully processed document: {doc_id}")
            
            # Return the updated Document
            return document

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            logger.exception(e)
            raise e


    def _get_ai_inference_service(self, context: "PipelineExecutionContext"):
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
    

    async def _process_document(self, data: dict, context: "PipelineExecutionContext", ai_model_inference_service):
        """
        Process a single document to extract text and images.
        
        :param data: Document data dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :return: processed data.
        """

        # get the chunks from the document
        chunks = data.get(self.content_iterator_field, [])
        if not chunks:
            logger.warning(f"No chunks found in document using field '{self.content_iterator_field}'.")
            return

        logger.debug(f"Processing {len(chunks)} chunk(s).")

        # Process each chunk
        for chunk in chunks:
            await self._process_chunk(chunk=chunk, 
                                      ai_model_inference_service=ai_model_inference_service)

        return data

    async def _process_chunk(self, chunk: dict, ai_model_inference_service):
        """
        Process a single chunk to apply the AI prompt and get the response.
        
        :param chunk: Chunk dictionary containing text and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: None
        """

        # get the first field in the chunk that has data
        chunk_field_value = None
        for field in self.chunk_fields_to_apply_prompt_on.split(","):
            if field in chunk and chunk[field]:
                chunk_field_value = chunk[field]
                break

        # Apply the AI prompt to the specified chunk field
        if chunk_field_value:
                    
            if isinstance(chunk_field_value, str) and chunk_field_value.strip():
                # Use the AI Model Inference Service to process the text
                # Prepare the user message with the chunk content
                if "{chunk_content}" in self.user_prompt:
                    # If the user prompt contains a placeholder for chunk content, format it
                    user_message = self.user_prompt.replace("{chunk_content}", chunk_field_value)
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
                    logger.debug(f"AI response for chunk {chunk.get('page_num', 'unknown')}: {ai_response}")
                        
                # Store the output in the specified output field
                chunk[self.output_field_name] = ai_response

            else:
                logger.warning(f"The value of {self.chunk_fields_to_apply_prompt_on} is not a string or is empty. Skipping this chunk.")
                chunk[self.output_field_name] = ""
        else:
            logger.warning(f"Chunk field(s) '{self.chunk_fields_to_apply_prompt_on}' not found in chunk: {chunk}. Skipping AI prompt application for this chunk.")
            chunk[self.output_field_name] = ""
            
