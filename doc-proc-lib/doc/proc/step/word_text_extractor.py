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

logger = logging.getLogger("doc.proc.step.word_text_extractor") # need to specify the logger name as this module is loaded dynamically


class WordTextExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)

        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.png_output_folder = self.settings.get("png_output_folder", "output_pngs")
        self.extract_images = self.settings.get("extract_images", True)
        self.extract_image_descriptions = self.settings.get("extract_image_descriptions", True)
        self.extract_tables = self.settings.get("extract_tables", True)
        self.max_chunk_size = self.settings.get("max_chunk_size", 4000)

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
            logger.debug(f"Initialized WordTextExtractorStep with settings: {self.settings} " \
                         f"PNG output folder: {self.png_output_folder}, Extract images: {self.extract_images}, Extract tables: {self.extract_tables} " \
                         f"Max chunk size: {self.max_chunk_size} " \
                         f"System prompt: {self.system_prompt}, User prompt: {self.user_prompt} " \
                         f"Max completion tokens: {self.max_completion_tokens}, Temperature: {self.temperature}, Top P: {self.top_p}, Frequency penalty: {self.frequency_penalty}, Presence penalty: {self.presence_penalty}.")


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your Word document text extraction logic

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
                # This will extend the document with extracted text and images for each section/chunk
                await self.process_document(document=document, 
                                            context=context, 
                                            ai_model_inference_service=ai_model_inference_service)

                _stats["successful_documents"] += 1

                if self.debug_mode:
                    logger.debug(f"Successfully processed document: {document}")
                else:
                    logger.info(f"Successfully processed document: {document.get('file_path', 'unknown')}")

            except Exception as e:
                logger.error(f"Error processing document {document}: {e}")
                _stats["failed_documents"] += 1

                if self.fail_step_on_document_error:
                    # If the step is configured to fail on document error, raise an exception
                    raise StepExecutionError(f"Failed to process document {document}: {e}")
        
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
        Process a single Word document to extract text and images.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance for processing images.
        :raises StepExecutionError: If the document processing fails.
        :raises ValueError: If the document does not contain a valid file path.
        :raises FileNotFoundError: If the Word file does not exist at the specified path.
        :return: None.
        """

        word_file_path = document.get("file_path")
        if not word_file_path:
            # do nothing
            logger.error("No input Word file path found in input data.")
            raise ValueError("No input Word file path found in input data. Please check the input data and try again.")

        # Check if the Word file exists
        if not os.path.exists(word_file_path):
            # do nothing
            logger.error(f"Word file not found: {word_file_path}.")
            raise FileNotFoundError(f"Word file not found: {word_file_path}. Please check the file path and try again.")

        # Check if the file is a Word document
        if not word_file_path.lower().endswith(('.docx', '.doc')):
            logger.error(f"Invalid file format: {word_file_path}. Expected a Word document (.docx or .doc).")
            raise ValueError(f"Invalid file format: {word_file_path}. Expected a Word document (.docx or .doc).")

        # STEP 1: Extract text content from Word document
        logger.debug(f"Extracting text from Word file {word_file_path}...")
        chunks_data = self.extract_word_content(word_file_path)

        # Step 2: Process extracted images using AI Model Inference Service if available
        if self.extract_images:
            logger.debug(f"Processing extracted images from Word document...")
            await self.process_extracted_images(chunks_data, ai_model_inference_service)

        # Update the document with the processed chunks data
        document['chunks'] = chunks_data

    
    def extract_word_content(self, word_file_path: str) -> List[dict]:
        """
        Extract text content from Word document.
        
        :param word_file_path: Path to the input Word file.
        :return: List of dictionaries containing extracted content.
        """
        
        try:
            from docx import Document
        except ImportError as e:
            logger.error("docx module is required for Word document processing. Please install it using 'pip install python-docx'.")
            raise StepExecutionError("docx module is required for Word document processing. Please install it using 'pip install python-docx'.")

        # Create output folder if it doesn't exist
        png_output_folder = self.png_output_folder
        os.makedirs(png_output_folder, exist_ok=True)

        # Open the Word document
        try:
            word_doc = Document(word_file_path)
        except Exception as e:
            logger.error(f"Error opening Word document {word_file_path}: {e}")
            raise StepExecutionError(f"Error opening Word document {word_file_path}: {e}")

        # Prepare a list to store the extracted content
        chunks_data = []
        chunk_counter = 1

        # Extract paragraphs and merge them into chunks
        current_chunk_text = []
        current_chunk_size = 0
        
        for paragraph in word_doc.paragraphs:
            if paragraph.text.strip():  # Skip empty paragraphs
                paragraph_text = paragraph.text.strip()
                paragraph_size = len(paragraph_text)
                
                # Check if adding this paragraph would exceed the max chunk size
                if current_chunk_size + paragraph_size + 1 > self.max_chunk_size and current_chunk_text:
                    # Create a chunk with the current accumulated paragraphs
                    chunk_text = '\n'.join(current_chunk_text)
                    chunk_id = self.generate_sha1_hash(f"{os.path.basename(word_file_path)}_paragraph_chunk_{chunk_counter}")
                    
                    chunk_data = {
                        'input_file_path': word_file_path,
                        'chunk_id': chunk_id,
                        'chunk_type': 'paragraph',
                        'chunk_num': chunk_counter,
                        'text': chunk_text,
                        'raw_text': chunk_text
                    }
                    
                    chunks_data.append(chunk_data)
                    chunk_counter += 1
                    
                    # Start a new chunk with the current paragraph
                    current_chunk_text = [paragraph_text]
                    current_chunk_size = paragraph_size
                else:
                    # Add paragraph to the current chunk
                    current_chunk_text.append(paragraph_text)
                    current_chunk_size += paragraph_size + 1  # +1 for the newline character
        
        # Add any remaining paragraphs as the final chunk
        if current_chunk_text:
            chunk_text = '\n'.join(current_chunk_text)
            chunk_id = self.generate_sha1_hash(f"{os.path.basename(word_file_path)}_paragraph_chunk_{chunk_counter}")
            
            chunk_data = {
                'input_file_path': word_file_path,
                'chunk_id': chunk_id,
                'chunk_type': 'paragraph',
                'chunk_num': chunk_counter,
                'text': chunk_text,
                'raw_text': chunk_text
            }
            
            chunks_data.append(chunk_data)
            chunk_counter += 1

        # Extract tables if enabled
        if self.extract_tables:
            for table_idx, table in enumerate(word_doc.tables):
                table_text = self.extract_table_text(table)
                if table_text.strip():
                    chunk_id = self.generate_sha1_hash(f"{os.path.basename(word_file_path)}_table_{table_idx + 1}")
                    
                    chunk_data = {
                        'input_file_path': word_file_path,
                        'chunk_id': chunk_id,
                        'chunk_type': 'table',
                        'chunk_num': chunk_counter,
                        'text': table_text.strip(),
                        'raw_text': table_text.strip()
                    }
                    
                    chunks_data.append(chunk_data)
                    chunk_counter += 1

        # Extract images if enabled
        if self.extract_images:
            try:
                self.extract_images_from_document(word_doc, word_file_path, chunks_data, chunk_counter)
            except Exception as e:
                logger.warning(f"Error extracting images from Word document {word_file_path}: {e}")

        return chunks_data


    def extract_table_text(self, table) -> str:
        """
        Extract text from a Word table.
        
        :param table: Word table object.
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


    def extract_images_from_document(self, doc, word_file_path: str, chunks_data: List[dict], chunk_counter: int):
        """
        Extract images from Word document and save them as PNG files.
        
        :param doc: Word document object.
        :param word_file_path: Path to the Word file.
        :param chunks_data: List to append image chunk data.
        :param chunk_counter: Current chunk counter.
        """
        png_output_folder = self.png_output_folder
        
        # Access the document's relationships to find images
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    # Get the image data
                    image_data = rel.target_part.blob
                    
                    # Generate filename
                    image_filename = f"image_{chunk_counter}.png"
                    image_path = os.path.join(png_output_folder, image_filename)
                    
                    # Save the image
                    with open(image_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    # Create chunk data for the image
                    chunk_id = self.generate_sha1_hash(f"{os.path.basename(word_file_path)}_image_{chunk_counter}")
                    
                    chunk_data = {
                        'input_file_path': word_file_path,
                        'chunk_id': chunk_id,
                        'chunk_type': 'image',
                        'chunk_num': chunk_counter,
                        'png': image_path,
                        'text': '',
                        'raw_text': ''
                    }
                    
                    chunks_data.append(chunk_data)
                    chunk_counter += 1
                    
                except Exception as e:
                    logger.warning(f"Error extracting image from Word document: {e}")
                    continue


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
