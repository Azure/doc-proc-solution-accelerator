import base64
import hashlib
import os
import re
import logging
from typing import List

import pymupdf
from azure.ai.inference.models import (
        SystemMessage,
        UserMessage,
        TextContentItem,
        ImageContentItem,
        ImageUrl,
        ImageDetailLevel,
    )

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig

logger = logging.getLogger("doc.proc.step.pdf_text_extractor") # need to specify the logger name as this module is loaded dynamically


class PDFTextExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.png_output_folder = self.settings.get("png_output_folder", "output_pngs")
        self.pages_to_convert = self.settings.get("num_pages", -1)  # -1 means all pages

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
            logger.debug(f"Initialized PDFTextExtractorStep with settings: {self.settings} " \
                         f"PNG output folder: {self.png_output_folder}, Pages to convert: {self.pages_to_convert} " \
                         f"System prompt: {self.system_prompt}, User prompt: {self.user_prompt} " \
                         f"Max completion tokens: {self.max_completion_tokens}, Temperature: {self.temperature}, Top P: {self.top_p}, Frequency penalty: {self.frequency_penalty}, Presence penalty: {self.presence_penalty}.")


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your PDF to PNG conversion logic

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
            "skipped_documents": 0,
            "failed_documents": 0,
        }

        # get documents from input data
        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            logger.warning(f"No documents found in input data: {input_data.data}. Expected a list of documents.")
            return StepInputOutput(summary_data=
                                    {
                                        **input_data.summary_data, f"{self.name}_stats": _stats
                                    }, 
                               data=
                                    {
                                        **input_data.data
                                    })
        
        _stats["total_documents"] = len(documents)        

        # Iterate through each filtered document in the input data
        logger.info(f"Processing {len(documents)} documents...")
            
        for document in documents:
            try:
                if self.debug_mode:
                    logger.debug(f"Processing document: {document}")
                
                # Check if the document is a dictionary and has the 'file_path' key
                if not isinstance(document, dict) or 'file_path' not in document:
                    raise ValueError(f"Invalid document format: {document}. Expected a dictionary with 'file_path' key.")
                
                # Evaluate condition if present
                if self.condition:
                    condition_met = self.evaluate_document_condition(document, input_data)
                    if not condition_met:
                        _stats["skipped_documents"] += 1
                        logger.info(f"Document skipped due to condition not met: {self.condition}")
                        continue
            
                # Process each document
                # This will extend the document with extracted text and images for each page/chunk
                await self.process_document(document=document, 
                                            context=context, 
                                            ai_model_inference_service=ai_model_inference_service)

                _stats["successful_documents"] += 1

                if self.debug_mode:
                    logger.debug(f"Successfully processed document: {document}")
                else:
                    logger.info(f"Successfully processed document: {document.get('file_path', 'unknown')}")

            except Exception as e:
                logger.error(f"Error processing document: {e}")
                _stats["failed_documents"] += 1

                if self.fail_step_on_document_error:
                    # If the step is configured to fail on document error, raise an exception
                    raise StepExecutionError(f"Failed to process document: {e}")

        logger.info(f"Processed {_stats['total_documents']} total documents. Successful: {_stats['successful_documents']}, Skipped: {_stats['skipped_documents']}, Failed: {_stats['failed_documents']}.")
        
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
        if not context or not hasattr(context, 'get_service'):
            logger.error("Invalid context provided. Cannot retrieve AI Model Inference Service.")
            return None

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
        :param ai_model_inference_service: AI Model Inference Service instance for processing images.
        :raises StepExecutionError: If the document processing fails.
        :raises ValueError: If the document does not contain a valid file path.
        :raises FileNotFoundError: If the PDF file does not exist at the specified path.
        :return: None.
        """

        pdf_file_path = document.get("file_path")
        if not pdf_file_path:
            # do nothing
            logger.error("No input PDF file path found in input data.")
            raise ValueError("No input PDF file path found in input data. Please check the input data and try again.")

        # Check if the PDF file exists
        if not os.path.exists(pdf_file_path):
            # do nothing
            logger.error(f"PDF file not found: {pdf_file_path}.")
            raise FileNotFoundError(f"PDF file not found: {pdf_file_path}. Please check the file path and try again.")


        # STEP 1: Convert PDF to PNG
        logger.debug(f"Converting PDF file {pdf_file_path} to PNG images...")
        chunks_data = self.convert_pdf_to_png(pdf_file_path)

        # Step 2: Convert PNG files to Markdown using AI Model Inference Service
        logger.debug(f"Converting {len(chunks_data)} PNG files to Markdown...")

        for chunk in chunks_data:

            if 'png' not in chunk:
                logger.warning(f"PNG file path not found in chunk data: {chunk}. Skipping conversion.")
                continue
                    
            # Check if the PNG file exists
            if not os.path.exists(chunk['png']):
                logger.warning(f"PNG file not found: {chunk['png']}. Skipping conversion.")
                continue

            try:    
                # # Convert the PNG to base64
                # png_base64 = self.convert_png_to_base64(chunk['png'])                
                # chunk['page_image_base64'] = png_base64
                # Call the AI Model Inference Service chat completion method with the PNG file

                markdown = self.convert_png_to_markdown(chunk['png'], ai_model_inference_service)
                chunk['markdown'] = markdown

                # Extract text sections from the markdown
                if markdown:
                    chunk['page_text'] = self.extract_text_section(markdown)
                    chunk['page_image_descriptions'] = self.extract_image_sections(markdown)
                    chunk['text'] = chunk.get('page_text', '') + chunk.get('page_image_descriptions', '')  # Append to existing text if any

            except Exception as e:
                logger.warning(f"Error converting PNG file {chunk['png']} to Markdown: {e}. Skipping this PNG file.")
                continue

        # Update the document with the processed chunks data
        document['chunks'] = chunks_data

    
    def convert_pdf_to_png(self, pdf_file_path: str) -> List[dict]:
        """
        Convert PDF pages to PNG images.
        
        :param pdf_file_path: Path to the input PDF file.
        :return: List of dictionaries containing page number and PNG file path.
        """
        
        png_output_folder = self.png_output_folder
        # Create output folder if it doesn't exist
        os.makedirs(png_output_folder, exist_ok=True)

        doc = pymupdf.open(pdf_file_path)

        if self.pages_to_convert == -1 or self.pages_to_convert > len(doc):
            self.pages_to_convert = len(doc)

        # Prepare a list to store the paths of the saved PNG files
        chunks_data = []

        # Iterate through pages and save as PNG
        for page_num in range(0, self.pages_to_convert):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            png_file_path = f'{png_output_folder}/page_{page_num+1}.png'
            pix.save(png_file_path)

            # generate a unique identifier for the page by hashing the file path and page number
            page_id = self.generate_sha1_hash(f"{os.path.basename(pdf_file_path)}_page_{page_num+1}")

            # Append the page number and PNG file path to the list
            chunks_data.append({'input_file_path': pdf_file_path, 'chunk_id': page_id, 'chunk_num': page_num+1, 'chunk_type': 'page', 'page_num': page_num+1, 'png': png_file_path})

        return chunks_data


    def convert_png_to_base64(self, png_path: str) -> str:
        """
        Convert a PNG file to a base64 encoded string.
        
        :param png_path: Path to the PNG file.
        :return: Base64 encoded string of the PNG file.
        """
        with open(png_path, "rb") as png_file:
            png_data = png_file.read()
            return base64.b64encode(png_data).decode('ascii')


    def convert_png_to_markdown(self, png_file_path: str, ai_model_inference_service) -> str:
        """
        Convert a PNG file to Markdown using AI Model Inference Service.
        
        :param png_file_path: Path to the input PNG file.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Markdown content generated from the PNG file.
        """
        # Prepare the chat completion request
        chat_completion_messages = [
            SystemMessage(content=self.system_prompt),
            UserMessage([
                TextContentItem(text=self.user_prompt),
                ImageContentItem(
                    image_url=ImageUrl.load(
                        image_file=png_file_path,
                        image_format="png",
                        detail=ImageDetailLevel.HIGH,
                    ),
                ),
            ],)
        ]

        response = ai_model_inference_service.run_chat_completion(messages=chat_completion_messages,
                                                                  max_completion_tokens=self.max_completion_tokens,
                                                                  temperature=self.temperature,
                                                                  top_p=self.top_p,
                                                                  frequency_penalty=self.frequency_penalty,
                                                                  presence_penalty=self.presence_penalty)
        
        return response.choices[0].message.content


    def extract_text_section(self, markdown:str):
        """
        Extract text section from the markdown content.
        
        :param markdown: Markdown content as a string.
        :return: Extracted the text section.
        """
        
        # Split the markdown by the separator '==Extracted-Text=='
        # and remove any leading/trailing whitespace from each line
        if not markdown:
            return []

        pattern = r'==Extracted-Text==\s*(.*?)\s*==End-Extracted-Text=='
        match = re.search(pattern, markdown, re.DOTALL)
        if match:
            markdown = match.group(1)
            return markdown
        
        return ""


    def extract_image_sections(self, markdown: str) -> str:
        """
        Extract image sections from the markdown content.

        :param markdown: Markdown content as a string.
        :return: Extracted image sections.
        """
        # Use a regular expression to find image descriptions
        image_pattern = r'!\[.*?\]\((.*?)\)'
        pattern = r'==Image-Descriptions==\s*(.*?)\s*==End-Image-Descriptions=='
        match = re.search(pattern, markdown, re.DOTALL)
        if match:
            markdown = match.group(1)
            return markdown
        
        return ""
