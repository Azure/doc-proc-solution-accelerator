import base64
import hashlib
import os
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
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput

logger = logging.getLogger("doc.proc.step.pdf_text_extractor") # need to specify the logger name as this module is loaded dynamically

class PDFTextExtractorStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, debug_mode: bool = False, services: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, debug_mode=debug_mode, services=services, settings=settings, **kwargs)

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
            logger.debug(f"Initialized PDFTextExtractorStep with settings: {self.settings}")
            logger.debug(f"PNG output folder: {self.png_output_folder}, Pages to convert: {self.pages_to_convert}")
            logger.debug(f"System prompt: {self.system_prompt}, User prompt: {self.user_prompt}")
            logger.debug(f"Max completion tokens: {self.max_completion_tokens}, Temperature: {self.temperature}, Top P: {self.top_p}, Frequency penalty: {self.frequency_penalty}, Presence penalty: {self.presence_penalty}")


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

    def generate_md5_hash(self, input_string):
        """
        Generates a md5 hash from a given string.
        """
        # Encode the string to bytes, as hash functions operate on bytes
        encoded_string = input_string.encode('utf-8')
        # Create a MD5 hash object
        md5_hash = hashlib.md5()
        # Update the hash object with the encoded string
        md5_hash.update(encoded_string)
        # Get the hexadecimal representation of the hash
        return md5_hash.hexdigest()

    
    def convert_png_to_base64(self, png_path: str) -> str:
        """
        Convert a PNG file to a base64 encoded string.
        
        :param png_path: Path to the PNG file.
        :return: Base64 encoded string of the PNG file.
        """
        with open(png_path, "rb") as png_file:
            png_data = png_file.read()
            return base64.b64encode(png_data).decode('ascii')


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
            page_id = self.generate_md5_hash(f"{os.path.basename(pdf_file_path)}_page_{page_num+1}")

            # Append the page number and PNG file path to the list
            chunks_data.append({'input_file_path': pdf_file_path, 'page_id': page_id, 'page_num': page_num+1, 'png': png_file_path})

        return chunks_data


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


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your PDF to PNG conversion logic here
        pdf_file_path = input_data.data.get("input_pdf_file")
        if not pdf_file_path:
            # do nothing
            logger.warning("No input PDF file path found in input data. Returning original input data.")
            # Return the original input data without any changes
            return StepInputOutput(summary_data=input_data.summary_data, data=input_data.data)

        # Check if the PDF file exists
        if not os.path.exists(pdf_file_path):
            # do nothing
            logger.warning(f"PDF file not found: {pdf_file_path}. Returning original input data.")
            return StepInputOutput(summary_data=input_data.summary_data, data=input_data.data)

        # get Azure AI Model Inference Service from context
        ai_model_inference_service = self.get_ai_inference_service(context)
        if not ai_model_inference_service:
            logger.error("Azure AI Model Inference Service not found in context.")
            raise StepExecutionError("Azure AI Model Inference Service not found in context.")

        
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

            except Exception as e:
                logger.warning(f"Error converting PNG file {chunk['png']} to Markdown: {e}. Skipping this PNG file.")
                continue


        # Return the updated StepInputOutput
        return StepInputOutput(summary_data=
                                    {
                                        **input_data.summary_data
                                    }, 
                               data=
                                    {
                                        **input_data.data,
                                        "chunks_data": chunks_data
                                    })
    

    