import os
import base64
import logging
import hashlib
import json
import tiktoken

from typing import List, Dict, Any

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

logger = logging.getLogger("doc.proc.step.azure_doc_intelligence_extractor") # need to specify the logger name as this module is loaded dynamically


class AzureDocumentIntelligenceExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.model_id = self.settings.get("model_id", "prebuilt-layout")
        self.extract_tables = self.settings.get("extract_tables", True)
        self.extract_key_value_pairs = self.settings.get("extract_key_value_pairs", True)
        self.extract_paragraphs = self.settings.get("extract_paragraphs", True)
        self.chunk_by_pages = self.settings.get("chunk_by_pages", True)
        self.output_format = self.settings.get("output_format", "markdown")  # structured, markdown, json

        self.encoding = tiktoken.get_encoding("cl100k_base")

        if self.debug_mode:
            logger.debug(f"Initialized AzureContentUnderstandingExtractorStep with settings: {self.settings} " \
                         f"Model ID: {self.model_id}, Extract tables: {self.extract_tables}, Extract key-value pairs: {self.extract_key_value_pairs} " \
                         f"Extract paragraphs: {self.extract_paragraphs}, Chunk by pages: {self.chunk_by_pages}" \
                         f"Output format: {self.output_format}.")
            
    async def process_document(self, document, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState, **kwargs):
        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {document}")
            
            # Check if the document is a dictionary
            if not isinstance(document, dict):
                logger.warning(f"Invalid document format: {document}. Skipping.")
                return
        
            # Process each document
            # This will extend the document with extracted content using Azure Document Intelligence
            await self.process_document_core(document=document,context=context)

            if self.debug_mode:
                logger.debug(f"Successfully processed document: {document.get('file_path')}")
            else:
                logger.info(f"Successfully processed document: {document.get('file_path')}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")

            if self.fail_step_on_document_error:
                raise StepExecutionError(f"Failed to process document: {e}")

    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState, **kwargs) -> StepInputOutput:
        # Implement document processing using Azure Content Understanding

        # Check if input_data has the required data structure
        if not input_data or not isinstance(input_data, StepInputOutput) or not hasattr(input_data, 'data') or input_data.data is None:
            logger.error(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")
            raise StepExecutionError(f"Invalid input data: {input_data}. Expected StepInputOutput instance.")

        # get Azure Document Intelligence Service from context
        self.doc_intel_service = self.get_document_intelligence_service(context)
        if not self.doc_intel_service:
            logger.error("Azure Document Intelligence Service not found in context.")
            raise StepExecutionError("Azure Document Intelligence Service not found in context.")
        
        document = input_data.data.get("documents")[0]
        await self.process_document(document, context, request, state)
        
        # Return the updated StepInputOutput
        return StepInputOutput(summary_data={}, 
                               data={**input_data.data}
                               )
    

    def get_document_intelligence_service(self, context: "PipelineExecutionContext"):
        """
        Get the Azure Document Intelligence Service from the context.

        :param context: PipelineExecutionContext instance.
        :return: Azure Document Intelligence Service instance.
        """
        if not context or not hasattr(context, 'get_service'):
            logger.error("Invalid context provided. Cannot retrieve Azure Content Understanding Service.")
            return None

        for name in self.services:
            cs = context.get_service(name)
            if cs and cs.type == 'azure_document_intelligence':
                return cs

        return None


    async def process_document_core(self, document: dict, context: "PipelineExecutionContext"):
        """
        Process a single document using Azure Document Intelligence service.

        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param doc_intell_service: Azure Document Intelligence Service instance.
        :raises StepExecutionError: If the document processing fails.
        :raises ValueError: If the document does not contain a valid file path.
        :raises FileNotFoundError: If the file does not exist at the specified path.
        :return: None.
        """

        # Check if the file is a supported format
        supported_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'docx', 'xlsx', 'pptx', 'heic']
        file_extension = document.get("document_type").get("primary_type")
        if file_extension not in supported_extensions:
            logger.warning(f"File format '{file_extension}' may not be supported. Supported formats: {supported_extensions}")

        logger.debug(f"Processing document: {document.get('content_uri')} using model: {self.model_id}")

        try:
            # Read file as bytes
            file_bytes = document.get("content")

            if document.get("encoding") == "base64":
                file_bytes = base64.b64decode(file_bytes)

            # Analyze document using Azure Document Intelligence
            analysis_result = await self.doc_intel_service.analyze_document_from_bytes(
                document_bytes=file_bytes,
                model_id=self.model_id,
                output_content_format="markdown" if self.output_format == "markdown" else "text"
            )

            if(self.debug_mode):
                #with open(f"f_analysis_result.json", 'w') as f:
                #    json.dump(analysis_result, f, indent=2)
                logger.debug(f"Analysis result for {document.get('content_uri')}: {json.dumps(analysis_result, indent=2)}")
            
            # Process and structure the results
            chunks_data = self._process_analysis_results(analysis_result, document.get("content_uri"))

            # Update the document with the processed chunks data
            document['chunks'] = chunks_data

            if self.debug_mode:
                logger.debug(f"Extracted {len(chunks_data)} chunks from document: {document.get('content_uri')}")

        except Exception as e:
            logger.error(f"Error analyzing document {document.get('content_uri')}: {e}")
            raise StepExecutionError(f"Error analyzing document {document.get('content_uri')}: {e}")

    def _process_analysis_results(self, analysis_result: Dict[str, Any], file_path: str) -> List[dict]:
        """
        Process Azure Content Understanding analysis results into chunks.
        
        :param analysis_result: Analysis result from Azure Content Understanding
        :param file_path: Path to the original file
        :return: List of chunk dictionaries
        """
        chunks_data = []
        chunk_counter = 1

        if self.chunk_by_pages:
            # Create chunks by pages
            chunks_data.extend(self._create_page_chunks(analysis_result, file_path, chunk_counter))
            chunk_counter += len(chunks_data)
        else:
            # Create a single chunk with all content
            chunks_data.extend(self._create_document_chunk(analysis_result, file_path, chunk_counter))
            chunk_counter += len(chunks_data)

        # Add table chunks if enabled
        if self.extract_tables and analysis_result.get('tables'):
            table_chunks = self._create_table_chunks(analysis_result, file_path, chunk_counter)
            chunks_data.extend(table_chunks)
            chunk_counter += len(table_chunks)

        # Add key-value pair chunks if enabled
        if self.extract_key_value_pairs and analysis_result.get('key_value_pairs'):
            kv_chunks = self._create_key_value_chunks(analysis_result, file_path, chunk_counter)
            chunks_data.extend(kv_chunks)

        return chunks_data

    def _create_page_chunks(self, analysis_result: Dict[str, Any], file_path: str, start_chunk_counter: int) -> List[dict]:
        """Create chunks for each page."""
        chunks = []
        
        for i, page in enumerate(analysis_result.get('pages', [])):
            page_number = page.get('page_number', i + 1)
            
            # Extract text from page lines
            page_text = self._extract_page_text(page)
            
            if page_text.strip():  # Only create chunk if there's content
                #chunk_id = self.generate_sha1_hash(f"{os.path.basename(file_path)}_page_{page_number}")
                chunk_id = page_number

                tokens = self.encoding.encode(page_text)

                chunk_data = {
                    'input_file_path': file_path,
                    'chunk_id': chunk_id,
                    'chunk_type': 'page',
                    'chunk_num': start_chunk_counter + i,
                    'page_num': page_number,
                    'text': page_text,
                    'length' : len(tokens),
                    'size' : len(tokens),
                    'raw_text': page_text,
                    'structured_content': self._format_page_content(page, analysis_result) if self.output_format == 'structured' else None,
                    'confidence': self._calculate_page_confidence(page)
                }
                
                chunks.append(chunk_data)
        
        return chunks

    def _create_document_chunk(self, analysis_result: Dict[str, Any], file_path: str, chunk_counter: int) -> List[dict]:
        """Create a single chunk for the entire document."""
        chunks = []
        
        # Use the main content from the analysis result
        document_text = analysis_result.get('content', '')
        
        if document_text.strip():
            #chunk_id = self.generate_sha1_hash(f"{os.path.basename(file_path)}_document")
            chunk_id = chunk_counter
            
            chunk_data = {
                'input_file_path': file_path,
                'chunk_id': chunk_id,
                'chunk_type': 'document',
                'chunk_num': chunk_counter,
                'text': document_text,
                'raw_text': document_text,
                'structured_content': analysis_result if self.output_format == 'structured' else None,
                'total_pages': len(analysis_result.get('pages', [])),
                'confidence': self._calculate_document_confidence(analysis_result)
            }
            
            chunks.append(chunk_data)
        
        return chunks

    def _create_table_chunks(self, analysis_result: Dict[str, Any], file_path: str, start_chunk_counter: int) -> List[dict]:
        """Create chunks for tables."""
        chunks = []
        
        for i, table in enumerate(analysis_result.get('tables', [])):
            table_text = self._format_table_text(table)
            
            if table_text.strip():
                chunk_id = self.generate_sha1_hash(f"{os.path.basename(file_path)}_table_{i + 1}")
                chunk_id = start_chunk_counter + i
                
                chunk_data = {
                    'input_file_path': file_path,
                    'chunk_id': chunk_id,
                    'chunk_type': 'table',
                    'chunk_num': start_chunk_counter + i,
                    'text': table_text,
                    'raw_text': table_text,
                    'table_data': table,
                    'row_count': table.get('row_count', 0),
                    'column_count': table.get('column_count', 0)
                }
                
                chunks.append(chunk_data)
        
        return chunks

    def _create_key_value_chunks(self, analysis_result: Dict[str, Any], file_path: str, start_chunk_counter: int) -> List[dict]:
        """Create chunks for key-value pairs."""
        chunks = []
        
        kv_pairs = analysis_result.get('key_value_pairs', [])
        if kv_pairs:
            # Group all key-value pairs into a single chunk
            kv_text = self._format_key_value_text(kv_pairs)
            
            if kv_text.strip():
                chunk_id = self.generate_sha1_hash(f"{os.path.basename(file_path)}_key_values")
                chunk_id = start_chunk_counter
                
                chunk_data = {
                    'input_file_path': file_path,
                    'chunk_id': chunk_id,
                    'chunk_type': 'key_value_pairs',
                    'chunk_num': start_chunk_counter,
                    'text': kv_text,
                    'raw_text': kv_text,
                    'key_value_data': kv_pairs,
                    'total_pairs': len(kv_pairs)
                }
                
                chunks.append(chunk_data)
        
        return chunks

    def _extract_page_text(self, page: Dict[str, Any]) -> str:
        """Extract text from pages."""
        text_items = page.get('lines', []) or page.get('paragraphs', []) or page.get('words', [])

        return '\n'.join([item.get('content', '') for item in text_items])

    def _format_page_content(self, page: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format page content in structured format."""
        return {
            'page_number': page.get('page_number', 1),
            'word_count': len(page.get('words', [])),
            'line_count': len(page.get('lines', [])),
            'words': page.get('words', []),
            'lines': page.get('lines', [])
        }

    def _format_table_text(self, table: Dict[str, Any]) -> str:
        """Format table data as text."""
        if self.output_format == 'markdown':
            return self._table_to_markdown(table)
        else:
            return self._table_to_text(table)

    def _table_to_markdown(self, table: Dict[str, Any]) -> str:
        """Convert table to markdown format."""
        cells = table.get('cells', [])
        if not cells:
            return ""

        # Group cells by row
        rows = {}
        for cell in cells:
            row_idx = cell.get('row_index', 0)
            col_idx = cell.get('column_index', 0)
            if row_idx not in rows:
                rows[row_idx] = {}
            rows[row_idx][col_idx] = cell.get('content', '')

        # Generate markdown table
        markdown_lines = []
        for row_idx in sorted(rows.keys()):
            row_cells = rows[row_idx]
            row_content = ' | '.join([row_cells.get(col_idx, '') for col_idx in sorted(row_cells.keys())])
            markdown_lines.append(f"| {row_content} |")
            
            # Add header separator after first row
            if row_idx == 0:
                separator = ' | '.join(['---' for _ in range(len(row_cells))])
                markdown_lines.append(f"| {separator} |")

        return '\n'.join(markdown_lines)

    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """Convert table to plain text format."""
        cells = table.get('cells', [])
        if not cells:
            return ""

        # Group cells by row
        rows = {}
        for cell in cells:
            row_idx = cell.get('row_index', 0)
            col_idx = cell.get('column_index', 0)
            if row_idx not in rows:
                rows[row_idx] = {}
            rows[row_idx][col_idx] = cell.get('content', '')

        # Generate text table
        text_lines = []
        for row_idx in sorted(rows.keys()):
            row_cells = rows[row_idx]
            row_content = '\t'.join([row_cells.get(col_idx, '') for col_idx in sorted(row_cells.keys())])
            text_lines.append(row_content)

        return '\n'.join(text_lines)

    def _format_key_value_text(self, kv_pairs: List[Dict[str, Any]]) -> str:
        """Format key-value pairs as text."""
        text_lines = []
        
        for kv_pair in kv_pairs:
            key_content = kv_pair.get('key', {}).get('content', '')
            value_content = kv_pair.get('value', {}).get('content', '')
            confidence = kv_pair.get('confidence', 1.0)
            
            if key_content or value_content:
                text_lines.append(f"{key_content}: {value_content} (confidence: {confidence:.2f})")

        return '\n'.join(text_lines)

    def _calculate_page_confidence(self, page: Dict[str, Any]) -> float:
        """Calculate average confidence for a page."""
        words = page.get('words', [])
        if not words:
            return 1.0
        
        total_confidence = sum([word.get('confidence', 1.0) for word in words])
        return total_confidence / len(words)

    def _calculate_document_confidence(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate average confidence for the entire document."""
        pages = analysis_result.get('pages', [])
        if not pages:
            return 1.0
        
        total_confidence = sum([self._calculate_page_confidence(page) for page in pages])
        return total_confidence / len(pages)
