import base64
import hashlib
import os
import re
import logging
from typing import List

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

logger = logging.getLogger("doc.proc.step.ai_pptx_text_extractor") # need to specify the logger name as this module is loaded dynamically


class AIPowerPointTextExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.png_output_folder = self.settings.get("png_output_folder", "./tmp/pptx_output/pngs")
        self.extract_images = self.settings.get("extract_images", True)
        self.extract_image_descriptions = self.settings.get("extract_image_descriptions", True)
        self.extract_tables = self.settings.get("extract_tables", True)
        self.extract_shapes = self.settings.get("extract_shapes", False)
        self.slides_to_convert = self.settings.get("num_slides", -1)  # -1 means all slides

        self.prompts = self.settings.get("prompts", {})

        # get prompts from settings
        self.system_prompt = self.prompts.get("system", self.settings.get("system_prompt", ""))
        if not self.system_prompt:
            logger.error("System prompt not found in settings.")
            raise StepExecutionError("System prompt not found in settings.")

        self.user_prompt = self.prompts.get("user", self.settings.get("user_prompt", ""))
        if not self.user_prompt:
            logger.error("User prompt not found in settings.")
            raise StepExecutionError("User prompt not found in settings.")

        self.max_completion_tokens = self.settings.get("max_completion_tokens", 4000)
        self.temperature = self.settings.get("temperature", 1.0)
        self.top_p = self.settings.get("top_p", 1.0)
        self.frequency_penalty = self.settings.get("frequency_penalty", 0.0)
        self.presence_penalty = self.settings.get("presence_penalty", 0.0)

        if self.debug_mode:
            logger.debug(f"Initialized PowerPointTextExtractorStep with settings: {self.settings} " \
                         f"PNG output folder: {self.png_output_folder}, Slides to convert: {self.slides_to_convert} " \
                         f"Extract images: {self.extract_images}, Extract tables: {self.extract_tables}, Extract shapes: {self.extract_shapes} " \
                         f"System prompt: {self.system_prompt}, User prompt: {self.user_prompt} " \
                         f"Max completion tokens: {self.max_completion_tokens}, Temperature: {self.temperature}, Top P: {self.top_p}, Frequency penalty: {self.frequency_penalty}, Presence penalty: {self.presence_penalty}.")


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your PowerPoint text extraction logic
        
        # get Azure AI Model Inference Service from context
        ai_model_inference_service = self.get_ai_inference_service(context)
        if not ai_model_inference_service:
            logger.error("Azure AI Model Inference Service not found in context.")
            raise StepExecutionError("Azure AI Model Inference Service not found in context.")

        # get documents from input data
        document = input_data.data.get("document", {})
            
        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {input_data.id}")

            # Process each document
            # This will extend the document with extracted text and images for each slide/chunk
            await self.process_document(document=document, 
                                        context=context, 
                                        ai_model_inference_service=ai_model_inference_service)

            if self.debug_mode:
                logger.debug(f"Successfully processed document: {input_data.id}")
            else:
                logger.info(f"Successfully processed document: {input_data.id}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")

            if self.fail_step_on_document_error:
                # If the step is configured to fail on document error, raise an exception
                raise StepExecutionError(f"Failed to process document: {e}")
        
        # Return the updated StepInputOutput
        return input_data

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
        Process a single PowerPoint document to extract text and images.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance for processing images.
        :raises StepExecutionError: If the document processing fails.
        :raises ValueError: If the document does not contain a valid file path.
        :raises FileNotFoundError: If the PowerPoint file does not exist at the specified path.
        :return: None.
        """

        # Check if the file is a PowerPoint document
        if not pptx_file_path.lower().endswith(('.pptx', '.ppt')):
            logger.error(f"Invalid file format: {pptx_file_path}. Expected a PowerPoint document (.pptx or .ppt).")
            raise ValueError(f"Invalid file format: {pptx_file_path}. Expected a PowerPoint document (.pptx or .ppt).")

        # STEP 1: Extract content from PowerPoint document
        logger.debug(f"Extracting content from PowerPoint file {pptx_file_path}...")
        chunks_data = self.extract_pptx_content(pptx_file_path)

        # Step 2: Process extracted images using AI Model Inference Service if available
        if self.extract_images:
            logger.debug(f"Processing extracted images from PowerPoint document...")
            await self.process_extracted_images(chunks_data, ai_model_inference_service)

        # Update the document with the processed chunks data
        document['chunks'] = chunks_data

    
    def extract_pptx_content(self, pptx_file_path: str) -> List[dict]:
        """
        Extract text content from PowerPoint document.
        
        :param pptx_file_path: Path to the input PowerPoint file.
        :return: List of dictionaries containing extracted content.
        """
        
        try:
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
        except ImportError as e:
            logger.error("pptx module is required for PowerPoint document processing. Please install it using 'pip install python-pptx'.")
            raise StepExecutionError("pptx module is required for PowerPoint document processing. Please install it using 'pip install python-pptx'.")

        # Create output folder if it doesn't exist
        png_output_folder = self.png_output_folder
        os.makedirs(png_output_folder, exist_ok=True)

        # Open the PowerPoint document
        try:
            presentation = Presentation(pptx_file_path)
        except Exception as e:
            logger.error(f"Error opening PowerPoint document {pptx_file_path}: {e}")
            raise StepExecutionError(f"Error opening PowerPoint document {pptx_file_path}: {e}")

        # Determine how many slides to process
        total_slides = len(presentation.slides)
        if self.slides_to_convert == -1 or self.slides_to_convert > total_slides:
            self.slides_to_convert = total_slides

        # Prepare a list to store the extracted content
        chunks_data = []
        chunk_counter = 1

        # Extract content from each slide
        for slide_idx in range(min(self.slides_to_convert, total_slides)):
            slide = presentation.slides[slide_idx]
            slide_number = slide_idx + 1
            
            # Extract text from slide
            slide_text = self.extract_slide_text(slide)
            if slide_text.strip():
                chunk_id = self.generate_sha1_hash(f"{os.path.basename(pptx_file_path)}_slide_{slide_number}_text")
                
                chunk_data = {
                    'input_file_path': pptx_file_path,
                    'chunk_id': chunk_id,
                    'chunk_type': 'slide_text',
                    'chunk_num': chunk_counter,
                    'slide_number': slide_number,
                    'text': slide_text.strip(),
                    'raw_text': slide_text.strip()
                }
                
                chunks_data.append(chunk_data)
                chunk_counter += 1

            # Extract tables from slide if enabled
            if self.extract_tables:
                tables = self.extract_slide_tables(slide)
                for table_idx, table_text in enumerate(tables):
                    if table_text.strip():
                        chunk_id = self.generate_sha1_hash(f"{os.path.basename(pptx_file_path)}_slide_{slide_number}_table_{table_idx + 1}")
                        
                        chunk_data = {
                            'input_file_path': pptx_file_path,
                            'chunk_id': chunk_id,
                            'chunk_type': 'table',
                            'chunk_num': chunk_counter,
                            'slide_number': slide_number,
                            'table_index': table_idx + 1,
                            'text': table_text.strip(),
                            'raw_text': table_text.strip()
                        }
                        
                        chunks_data.append(chunk_data)
                        chunk_counter += 1

            # Extract images from slide if enabled
            if self.extract_images:
                try:
                    image_chunks = self.extract_slide_images(slide, pptx_file_path, slide_number, chunk_counter)
                    chunks_data.extend(image_chunks)
                    chunk_counter += len(image_chunks)
                except Exception as e:
                    logger.warning(f"Error extracting images from slide {slide_number}: {e}")

        return chunks_data


    def extract_slide_text(self, slide) -> str:
        """
        Extract text from a PowerPoint slide.
        
        :param slide: PowerPoint slide object.
        :return: Extracted slide text.
        """
        text_content = []
        
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                text_content.append(shape.text.strip())
        
        return "\n".join(text_content)


    def extract_slide_tables(self, slide) -> List[str]:
        """
        Extract tables from a PowerPoint slide.
        
        :param slide: PowerPoint slide object.
        :return: List of extracted table texts.
        """
        from pptx.enum.shapes import MSO_SHAPE_TYPE
                
        tables = []
        
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.TABLE:
                table_text = self.extract_table_text(shape.table)
                if table_text.strip():
                    tables.append(table_text)
        
        return tables


    def extract_table_text(self, table) -> str:
        """
        Extract text from a PowerPoint table.
        
        :param table: PowerPoint table object.
        :return: Extracted table text.
        """
        table_text = []
        
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                row_text.append(cell_text)
            table_text.append(" | ".join(row_text))
        
        return "\n".join(table_text)


    def extract_slide_images(self, slide, pptx_file_path: str, slide_number: int, chunk_counter: int) -> List[dict]:
        """
        Extract images from a PowerPoint slide and save them as PNG files.
        
        :param slide: PowerPoint slide object.
        :param pptx_file_path: Path to the PowerPoint file.
        :param slide_number: Current slide number.
        :param chunk_counter: Current chunk counter.
        :return: List of image chunk data.
        """
        
        from pptx.enum.shapes import MSO_SHAPE_TYPE
        
        image_chunks = []
        png_output_folder = self.png_output_folder
        image_counter = 1
        
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE: # type: ignore
                try:
                    # Get the image data
                    image_data = shape.image.blob
                    
                    # Generate filename
                    image_filename = f"{os.path.basename(pptx_file_path)}_slide_{slide_number}_image_{image_counter}.png"
                    image_path = os.path.join(png_output_folder, image_filename)
                    
                    # Save the image
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    # Create chunk data for the image
                    chunk_id = self.generate_sha1_hash(f"{os.path.basename(pptx_file_path)}_slide_{slide_number}_image_{image_counter}")
                    
                    chunk_data = {
                        'input_file_path': pptx_file_path,
                        'chunk_id': chunk_id,
                        'chunk_type': 'image',
                        'chunk_num': chunk_counter + image_counter - 1,
                        'slide_number': slide_number,
                        'image_index': image_counter,
                        'png': image_path,
                        'text': '',
                        'raw_text': ''
                    }
                    
                    image_chunks.append(chunk_data)
                    image_counter += 1
                    
                except Exception as e:
                    logger.warning(f"Error extracting image {image_counter} from slide {slide_number}: {e}")
                    continue
        
        return image_chunks


    async def process_extracted_images(self, chunks_data: List[dict], ai_model_inference_service):
        """
        Process extracted images using AI Model Inference Service.
        
        :param chunks_data: List of chunk data containing image paths.
        :param ai_model_inference_service: AI Model Inference Service instance.
        """
        for chunk in chunks_data:
            if chunk.get('chunk_type') == 'image' and 'png' in chunk:
                
                # Check if the PNG file exists
                if not os.path.exists(chunk['png']):
                    logger.warning(f"PNG file not found: {chunk['png']}. Skipping conversion.")
                    continue

                try:
                    # Call the AI Model Inference Service to process the image
                    markdown = self.convert_png_to_markdown(chunk['png'], ai_model_inference_service)
                    chunk['markdown'] = markdown

                    # Extract text sections from the markdown
                    if markdown:
                        chunk['markdown_text'] = self.extract_text_section(markdown)
                        
                        if self.extract_image_descriptions:
                            chunk['markdown_image_descriptions'] = self.extract_image_sections(markdown)
                            chunk['text'] = chunk.get('markdown_text', '') + chunk.get('markdown_image_descriptions', '')  # Append to existing text if any
                        else:
                            chunk['text'] = chunk.get('markdown_text', '')
                            
                except Exception as e:
                    logger.warning(f"Error converting PNG file {chunk['png']} to Markdown: {e}. Skipping this PNG file.")
                    continue


    def generate_sha1_hash(self, input_string):
        """
        Generates a sha1 hash from a given string.
        """
        # Encode the string to bytes, as hash functions operate on bytes
        encoded_string = input_string.encode('utf-8')
        # Create a SHA1 hash object
        sha1_hash = hashlib.sha1()
        # Update the hash object with the encoded string
        sha1_hash.update(encoded_string)
        # Get the hexadecimal representation of the hash
        return sha1_hash.hexdigest()


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


    def extract_text_section(self, markdown: str):
        """
        Extract text section from the markdown content.
        
        :param markdown: Markdown content as a string.
        :return: Extracted the text section.
        """
        
        # Split the markdown by the separator '==Extracted-Text=='
        # and remove any leading/trailing whitespace from each line
        if not markdown:
            return ""

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
        pattern = r'==Image-Descriptions==\s*(.*?)\s*==End-Image-Descriptions=='
        match = re.search(pattern, markdown, re.DOTALL)
        if match:
            markdown = match.group(1)
            return markdown
        
        return ""
