import os
import logging
from typing import List
import hashlib

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document

logger = logging.getLogger("doc.proc.step.excel_text_extractor") # need to specify the logger name as this module is loaded dynamically


class ExcelTextExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.png_output_folder = self.settings.get("png_output_folder", "./tmp/excel_output/pngs")
        self.extract_images = self.settings.get("extract_images", False)  # Default to False if not specified
        self.extract_charts = self.settings.get("extract_charts", False)  # Default to False if not specified
        self.max_rows_per_sheet = self.settings.get("max_rows_per_sheet", -1)  # -1 means all rows
        self.max_columns_per_sheet = self.settings.get("max_columns_per_sheet", -1)  # -1 means all columns
        self.sheets_to_process = self.settings.get("sheets_to_process", [])  # Empty list means all sheets

        if self.debug_mode:
            logger.debug(f"Initialized ExcelTextExtractorStep with settings: {self.settings} " \
                         f"PNG output folder: {self.png_output_folder}, Extract images: {self.extract_images}, Extract charts: {self.extract_charts} " \
                         f"Max rows per sheet: {self.max_rows_per_sheet}, Max columns per sheet: {self.max_columns_per_sheet} " \
                         f"Sheets to process: {self.sheets_to_process}.")


    async def run(self, document: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        """
        Run the step processing logic for Excel text extraction.

        Args:
            document: Input document to analyze
            context: Pipeline execution context

        Returns:
            Document: Output with text extracted from Excel
        """

        # Check if document has the required data structure
        if not document or not isinstance(document, Document) or not hasattr(document, 'data') or document.data is None:
            logger.error(f"Invalid input document: {document}. Expected Document instance with 'data' attribute.")
            raise StepExecutionError(f"Invalid input document: {document}. Expected Document instance.")
        
        # get document from input data
        doc_to_process = document.data
        if not doc_to_process or not isinstance(doc_to_process, dict):
            logger.error(f"No document data found in input data: {document.data}. Expected a dictionary of fields.")
            raise StepExecutionError(f"No document data found in input data: {document.data}. Expected a dictionary of fields.")

        try:
            if self.debug_mode:
                logger.debug(f"Processing document: {doc_to_process}")

                
            doc_to_process = doc_to_process if isinstance(doc_to_process, dict) else {"file_path": doc_to_process}
            # Validate required fields - now only file_path is required
            if "file_path" not in doc_to_process:
                raise StepExecutionError(f"Invalid document format: {doc_to_process}. Document is missing the required 'file_path' field.")

            # Process the document
            # This will extend the document with extracted text and images for each sheet/chunk
            result_data = await self._process_document(document=doc_to_process, 
                                         context=context)

            logger.debug(f"Successfully processed document: {document.id}")
                
            # Return the updated Document
            return Document(summary_data = {**document.summary_data}, 
                            data = result_data)

        except Exception as e:
            logger.error(f"Error processing document {document}: {e}")
            raise e


    async def _process_document(self, document: dict, context: "PipelineExecutionContext"):
        """
        Process a single Excel document to extract text and images.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance for processing images.
        :raises StepExecutionError: If the document processing fails.
        :raises ValueError: If the document does not contain a valid file path.
        :raises FileNotFoundError: If the Excel file does not exist at the specified path.
        :return: None.
        """

        excel_file_path = document.get("file_path")
        if not excel_file_path:
            logger.error(f"No file path found in document: {document}")
            raise ValueError(f"No file path found in document: {document}")

        # Check if the Excel file exists
        if not os.path.exists(excel_file_path):
            logger.error(f"Excel file not found: {excel_file_path}")
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")

        # Check if the file is an Excel document
        if not excel_file_path.lower().endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
            logger.error(f"File is not an Excel document: {excel_file_path}")
            raise ValueError(f"File is not an Excel document: {excel_file_path}")

        # STEP 1: Extract text content from Excel document
        logger.debug(f"Extracting text from Excel file {excel_file_path}...")
        chunks_data = self._extract_excel_content(excel_file_path)

        # Update the document with the processed chunks data
        document['chunks'] = chunks_data
        
        return document

    
    def _extract_excel_content(self, excel_file_path: str) -> List[dict]:
        """
        Extract text content from Excel document.
        
        :param excel_file_path: Path to the input Excel file.
        :return: List of dictionaries containing extracted content.
        """
        
        try:
            import openpyxl
            from openpyxl.drawing.image import Image as OpenpyxlImage
        except ImportError:
            logger.error("openpyxl library is required for Excel processing. Please install it using: pip install openpyxl")
            raise StepExecutionError("openpyxl library is required for Excel processing. Please install it using: pip install openpyxl")

        # Create output folder if it doesn't exist
        png_output_folder = self.png_output_folder
        os.makedirs(png_output_folder, exist_ok=True)

        # Open the Excel document
        try:
            workbook = openpyxl.load_workbook(excel_file_path, data_only=True)
        except Exception as e:
            logger.error(f"Failed to open Excel file {excel_file_path}: {e}")
            raise StepExecutionError(f"Failed to open Excel file {excel_file_path}: {e}")

        # Determine which sheets to process
        sheet_names = workbook.sheetnames
        if self.sheets_to_process:
            sheets_to_process = [name for name in self.sheets_to_process if name in sheet_names]
            if not sheets_to_process:
                logger.warning(f"None of the specified sheets {self.sheets_to_process} found in workbook. Processing all sheets.")
                sheets_to_process = sheet_names
        else:
            sheets_to_process = sheet_names

        # Prepare a list to store the extracted content
        chunks_data = []
        chunk_counter = 1

        # Extract content from each sheet
        for sheet_name in sheets_to_process:
            logger.debug(f"Processing sheet: {sheet_name}")
            
            sheet = workbook[sheet_name]
            
            # Extract sheet data
            sheet_text = self._extract_sheet_text(sheet)
            
            if sheet_text.strip():  # Only add non-empty sheets
                chunk_id = self._generate_sha1_hash(f"{excel_file_path}_sheet_{sheet_name}_chunk_{chunk_counter}")
                
                chunk = {
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_counter,
                    "chunk_type": "sheet",
                    "sheet_name": sheet_name,
                    "text": sheet_text,
                    "input_file_path": excel_file_path
                }
                
                chunks_data.append(chunk)
                chunk_counter += 1

            # Extract images and charts if enabled
            if self.extract_images or self.extract_charts:
                image_chunks = self._extract_sheet_images_and_charts(sheet, excel_file_path, sheet_name, chunk_counter)
                chunks_data.extend(image_chunks)
                chunk_counter += len(image_chunks)

        return chunks_data


    def _extract_sheet_text(self, sheet) -> str:
        """
        Extract text from an Excel sheet.
        
        :param sheet: Excel sheet object.
        :return: Extracted sheet text.
        """
        text_content = []
        
        # Get the used range of the sheet
        max_row = sheet.max_row
        max_col = sheet.max_column
        
        # Apply limits if specified
        if self.max_rows_per_sheet > 0:
            max_row = min(max_row, self.max_rows_per_sheet)
        if self.max_columns_per_sheet > 0:
            max_col = min(max_col, self.max_columns_per_sheet)
        
        # Extract data row by row
        for row_num in range(1, max_row + 1):
            row_data = []
            for col_num in range(1, max_col + 1):
                cell = sheet.cell(row=row_num, column=col_num)
                cell_value = str(cell.value) if cell.value is not None else ""
                row_data.append(cell_value)
            
            # Only add non-empty rows
            row_text = "\t".join(row_data).strip()
            if row_text:
                text_content.append(row_text)
        
        return "\n".join(text_content)


    def _extract_sheet_images_and_charts(self, sheet, excel_file_path: str, sheet_name: str, chunk_counter: int) -> List[dict]:
        """
        Extract images and charts from an Excel sheet and save them as PNG files.
        
        :param sheet: Excel sheet object.
        :param excel_file_path: Path to the Excel file.
        :param sheet_name: Name of the current sheet.
        :param chunk_counter: Current chunk counter.
        :return: List of image chunk data.
        """
        image_chunks = []
        png_output_folder = self.png_output_folder
        image_counter = 1
        
        # Extract embedded images
        if hasattr(sheet, '_images') and sheet._images:
            for image in sheet._images:
                try:
                    # Generate a unique filename for the image
                    image_filename = f"excel_sheet_{sheet_name}_image_{image_counter}.png"
                    image_path = os.path.join(png_output_folder, image_filename)
                    
                    # Save the image
                    with open(image_path, "wb") as img_file:
                        img_file.write(image.ref.getvalue())
                    
                    chunk_id = self._generate_sha1_hash(f"{excel_file_path}_sheet_{sheet_name}_image_{image_counter}")
                    
                    chunk = {
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_counter + image_counter - 1,
                        "chunk_type": "image",
                        "sheet_name": sheet_name,
                        "image_path": image_path,
                        "input_file_path": excel_file_path
                    }
                    
                    image_chunks.append(chunk)
                    image_counter += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image from sheet {sheet_name}: {e}")
        
        # Extract charts (charts are more complex in openpyxl, this is a simplified approach)
        if self.extract_charts and hasattr(sheet, '_charts') and sheet._charts:
            for chart_idx, chart in enumerate(sheet._charts):
                try:
                    # For charts, we'll create a text representation since extracting chart images is complex
                    chart_text = f"Chart: {chart.title.text if chart.title else f'Chart {chart_idx + 1}'}"
                    if hasattr(chart, 'series') and chart.series:
                        chart_text += f"\nSeries: {len(chart.series)} data series"
                    
                    chunk_id = self._generate_sha1_hash(f"{excel_file_path}_sheet_{sheet_name}_chart_{chart_idx + 1}")
                    
                    chunk = {
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_counter + image_counter - 1,
                        "chunk_type": "chart",
                        "sheet_name": sheet_name,
                        "text": chart_text,
                        "input_file_path": excel_file_path
                    }
                    
                    image_chunks.append(chunk)
                    image_counter += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to extract chart from sheet {sheet_name}: {e}")
        
        return image_chunks
    

    

