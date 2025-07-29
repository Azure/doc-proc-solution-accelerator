import base64
import hashlib
import os
import re
import logging
from typing import List

import pymupdf

from azure.ai.inference.models import (
        SystemMessage,
        UserMessage
    )

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig

logger = logging.getLogger("doc.proc.step.custom_ai_prompt") # need to specify the logger name as this module is loaded dynamically

class CustomAIPromptStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        # Set default values for settings if not provided
        self.chunk_field_to_apply_prompt_on = self.settings.get("chunk_field_to_apply_prompt_on", "markdown_text")
        if not self.chunk_field_to_apply_prompt_on:
            logger.error("Chunk field to apply prompt on not found in settings.")
            raise ValueError("Chunk field to apply prompt on not found in settings.")

        self.output_field_name = self.settings.get("output_field_name", "custom_ai_prompt_output")
        if not self.output_field_name:
            logger.error("Output field name not found in settings.")
            raise ValueError("Output field name not found in settings.")

        # get prompts from settings
        self.prompts = self.settings.get("prompts", {})
        if not self.prompts:
            logger.error("No prompts found in settings.")
            raise StepExecutionError("No prompts found in settings.")

        self.system_prompt = self.prompts.get("system", "")
        if not self.system_prompt:
            logger.error("System prompt not found in settings.")
            raise StepExecutionError("System prompt not found in settings.")

        self.user_prompt = self.prompts.get("user", "")
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


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        """ Run the custom AI prompt step to process documents and apply AI prompts."""

        # Check if input_data has the required data structure
        if not input_data or not isinstance(input_data, StepInputOutput) or not hasattr(input_data, 'data') or input_data.data is None:
            logger.error(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
            raise StepExecutionError(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
        
        # get Azure AI Model Inference Service from context
        ai_model_inference_service = self.get_ai_inference_service(context)
        if not ai_model_inference_service:
            logger.error("Azure AI Model Inference Service not found in context.")
            raise StepExecutionError("Azure AI Model Inference Service not found in context.")

        _stats = {
            "total_documents": 0,
            "successful_documents": 0,
            "failed_documents": 0,
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

        # Iterate through each document in the input data
        logger.info(f"Processing {len(documents)} documents...")
        
        _stats["total_documents"] = len(documents)

        for document in documents:
            try:
                if self.debug_mode:
                    logger.debug(f"Processing document: {document}")

                # Check if the document is a dictionary
                if not isinstance(document, dict):
                    raise ValueError(f"Invalid document format: {document}. Expected a dictionary with attributes.")
                    
                # Process each document
                # This will extend the document with extracted text and images for each page/chunk
                await self.process_document(document=document, 
                                            context=context, 
                                            ai_model_inference_service=ai_model_inference_service)
                
                _stats["successful_documents"] += 1

                if self.debug_mode:
                    logger.debug(f"Successfully processed document: {document}")

            except Exception as e:
                logger.error(f"Error processing document: {e}")
                _stats["failed_documents"] += 1

                if self.fail_step_on_document_error:
                    # If the step is configured to fail on document error, raise an exception
                    raise StepExecutionError(f"Failed to process document: {e}")

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
    

    async def process_document(self, document: dict, context: "PipelineExecutionContext", ai_model_inference_service):
        """
        Process a single document to extract text and images.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :return: StepInputOutput with processed data.
        """

        # get the chunks from the document
        chunks = document.get("chunks", [])
        if not chunks:
            logger.warning(f"No chunks found in document.")
            raise StepExecutionError(f"No chunks found in document.")

        logger.debug(f"Processing {len(chunks)} chunks.")

        # Process each chunk
        for chunk in chunks:
            await self.process_chunk(chunk=chunk, 
                                     context=context, 
                                     ai_model_inference_service=ai_model_inference_service)               

            
    async def process_chunk(self, chunk: dict, context: "PipelineExecutionContext", ai_model_inference_service):
        """
        Process a single chunk to apply the AI prompt and get the response.
        
        :param chunk: Chunk dictionary containing text and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: None
        """
    
        # Apply the AI prompt to the specified chunk field
        if self.chunk_field_to_apply_prompt_on in chunk:
            chunk_field_value = chunk[self.chunk_field_to_apply_prompt_on]
                    
            if isinstance(chunk_field_value, str) and chunk_field_value.strip():
                # Use the AI Model Inference Service to process the text
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
                    logger.debug(f"AI response for chunk {chunk.get('page_num', 'unknown')}: {ai_response}")
                        
                # Store the output in the specified output field
                chunk[self.output_field_name] = ai_response

            else:
                logger.warning(f"The value of {self.chunk_field_to_apply_prompt_on} is not a string or is empty. Skipping this chunk.")
                chunk[self.output_field_name] = ""
        else:
            logger.warning(f"Chunk field '{self.chunk_field_to_apply_prompt_on}' not found in chunk: {chunk}. Skipping AI prompt application for this chunk.")
            chunk[self.output_field_name] = ""
            
