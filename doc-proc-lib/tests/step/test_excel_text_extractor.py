"""
Unit tests for the ExcelTextExtractorStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from doc.proc.step.excel_text_extractor import ExcelTextExtractorStep
from doc.proc.models import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestExcelTextExtractorStep:
    """Test cases for ExcelTextExtractorStep."""
    
    @pytest.fixture
    def excel_step_config(self):
        """Fixture for ExcelTextExtractorStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="excel_text_extractor",
            name="excel_extractor_instance",
            enabled=True,
            debug_mode=True,
            services=["ai_inference_service"],
            settings={
                "png_output_folder": "test_output",
                "extract_images": True,
                "extract_charts": True,
                "max_rows_per_sheet": 100,
                "max_columns_per_sheet": 50,
                "sheets_to_process": [],
                "prompts": {
                    "system": "You are an AI assistant that analyzes Excel content.",
                    "user": "Analyze this Excel content and extract key information."
                },
                "max_completion_tokens": 2000,
                "temperature": 0.7
            }
        )
    
    @pytest.fixture
    def excel_document_input(self):
        """Fixture for Excel document input."""
        return StepInputOutput(
            id="excel_test",
            summary_data={"total_documents": 1},
            data={
                "documents": [
                    {
                        "file_path": "/test/sample.xlsx",
                        "file_name": "sample.xlsx",
                        "file_size": 4096,
                        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "document_type": {
                            "primary_type": "excel",
                            "confidence": 0.98
                        }
                    }
                ]
            }
        )
    
    @pytest.fixture
    def mock_ai_service(self):
        """Fixture for mocked AI inference service."""
        mock_service = MagicMock()
        mock_service.type = 'azure_ai_inference'
        
        # Mock the response for chat completion
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "==Extracted-Text==\nExtracted content from Excel\n==End-Extracted-Text=="
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_service.run_chat_completion.return_value = mock_response
        
        return mock_service
    
    def test_excel_step_initialization(self, excel_step_config):
        """Test successful initialization of ExcelTextExtractorStep."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        assert step.step_catalog_id == "excel_text_extractor"
        assert step.name == "excel_extractor_instance"
        assert step.debug_mode is True
        assert step.extract_images is True
        assert step.extract_charts is True
        assert step.max_rows_per_sheet == 100
        assert step.max_columns_per_sheet == 50
        assert step.sheets_to_process == []
    
    def test_excel_step_initialization_no_prompts(self):
        """Test ExcelTextExtractorStep initialization without prompts raises error."""
        config = StepInstanceConfig(
            step_catalog_id="excel_text_extractor",
            name="excel_extractor_instance",
            settings={}  # No prompts
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            ExcelTextExtractorStep(config)
        assert "No prompts found in settings" in str(exc_info.value)
    
    def test_excel_step_initialization_no_system_prompt(self):
        """Test ExcelTextExtractorStep initialization without system prompt raises error."""
        config = StepInstanceConfig(
            step_catalog_id="excel_text_extractor",
            name="excel_extractor_instance",
            settings={
                "prompts": {
                    "user": "Test user prompt"
                    # Missing system prompt
                }
            }
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            ExcelTextExtractorStep(config)
        assert "System prompt not found in settings" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_excel_step_invalid_input_data(self, excel_step_config, mock_pipeline_context):
        """Test ExcelTextExtractorStep with invalid input data."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_excel_step_no_ai_service(self, excel_step_config, excel_document_input):
        """Test ExcelTextExtractorStep when AI service is not available."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Mock context without AI service
        mock_context = MagicMock()
        mock_context.get_service.return_value = None
        
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(excel_document_input, mock_context)
        assert "Azure AI Model Inference Service not found in context" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_excel_step_no_documents(self, excel_step_config, mock_pipeline_context, mock_ai_service):
        """Test ExcelTextExtractorStep with no documents."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Mock the AI service in context
        mock_pipeline_context.get_service.return_value = mock_ai_service
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        result = await step.run(step_input, mock_pipeline_context)
        
        # Should return empty result but not fail
        assert isinstance(result, StepInputOutput)
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 0
        assert stats["successful_documents"] == 0
        assert stats["failed_documents"] == 0
    
    @pytest.mark.asyncio
    @patch('doc.proc.step.excel_text_extractor.openpyxl')
    @patch('os.path.exists')
    @patch('os.makedirs')
    async def test_excel_step_successful_processing(self, mock_makedirs, mock_exists, mock_openpyxl, 
                                                  excel_step_config, excel_document_input, 
                                                  mock_pipeline_context, mock_ai_service):
        """Test successful Excel document processing."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Mock the AI service in context
        mock_pipeline_context.get_service.return_value = mock_ai_service
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock openpyxl
        mock_workbook = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.max_row = 2
        mock_sheet.max_column = 2
        
        # Mock cells
        mock_cell1 = MagicMock()
        mock_cell1.value = "Header 1"
        mock_cell2 = MagicMock()
        mock_cell2.value = "Header 2"
        mock_cell3 = MagicMock()
        mock_cell3.value = "Data 1"
        mock_cell4 = MagicMock()
        mock_cell4.value = "Data 2"
        
        def cell_side_effect(row, column):
            if row == 1 and column == 1:
                return mock_cell1
            elif row == 1 and column == 2:
                return mock_cell2
            elif row == 2 and column == 1:
                return mock_cell3
            elif row == 2 and column == 2:
                return mock_cell4
            return MagicMock(value=None)
        
        mock_sheet.cell.side_effect = cell_side_effect
        mock_sheet._images = []  # No images
        mock_sheet._charts = []  # No charts
        
        mock_workbook.sheetnames = ["Sheet1"]
        mock_workbook.__getitem__.return_value = mock_sheet
        mock_openpyxl.load_workbook.return_value = mock_workbook
        
        result = await step.run(excel_document_input, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Check stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] == 1
        assert stats["failed_documents"] == 0
        
        # Check that chunks were created
        documents = result.data["documents"]
        assert len(documents) == 1
        assert "chunks" in documents[0]
        chunks = documents[0]["chunks"]
        assert len(chunks) > 0
        
        # Check chunk content
        first_chunk = chunks[0]
        assert first_chunk["chunk_type"] == "sheet"
        assert first_chunk["sheet_name"] == "Sheet1"
        assert "Header 1\tHeader 2" in first_chunk["text_content"]
        assert "Data 1\tData 2" in first_chunk["text_content"]
    
    @pytest.mark.asyncio
    async def test_excel_step_invalid_document_format(self, excel_step_config, mock_pipeline_context, mock_ai_service):
        """Test ExcelTextExtractorStep with invalid document format."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Mock the AI service in context
        mock_pipeline_context.get_service.return_value = mock_ai_service
        
        step_input = StepInputOutput(
            summary_data={},
            data={
                "documents": [
                    "invalid_document_format"  # Not a dictionary
                ]
            }
        )
        
        result = await step.run(step_input, mock_pipeline_context)
        
        # Should handle error gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] == 0
        assert stats["failed_documents"] == 1
    
    @pytest.mark.asyncio
    @patch('os.path.exists')
    async def test_excel_step_file_not_found(self, mock_exists, excel_step_config, 
                                           excel_document_input, mock_pipeline_context, mock_ai_service):
        """Test ExcelTextExtractorStep when Excel file doesn't exist."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Mock the AI service in context
        mock_pipeline_context.get_service.return_value = mock_ai_service
        
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        result = await step.run(excel_document_input, mock_pipeline_context)
        
        # Should handle error gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] == 0
        assert stats["failed_documents"] == 1
    
    @pytest.mark.asyncio
    @patch('os.path.exists')
    async def test_excel_step_invalid_file_extension(self, mock_exists, excel_step_config, 
                                                   mock_pipeline_context, mock_ai_service):
        """Test ExcelTextExtractorStep with invalid file extension."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        # Mock the AI service in context
        mock_pipeline_context.get_service.return_value = mock_ai_service
        
        # Mock file exists
        mock_exists.return_value = True
        
        step_input = StepInputOutput(
            data={
                "documents": [
                    {
                        "file_path": "/test/sample.txt"  # Not an Excel file
                    }
                ]
            }
        )
        
        result = await step.run(step_input, mock_pipeline_context)
        
        # Should handle error gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] == 0
        assert stats["failed_documents"] == 1
    
    def test_generate_sha1_hash(self, excel_step_config):
        """Test SHA1 hash generation."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        test_string = "test_string"
        hash_result = step.generate_sha1_hash(test_string)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 40  # SHA1 hash is 40 characters long
        
        # Same input should produce same hash
        hash_result2 = step.generate_sha1_hash(test_string)
        assert hash_result == hash_result2
    
    def test_extract_text_section(self, excel_step_config):
        """Test text section extraction from markdown."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        markdown = "==Extracted-Text==\nThis is extracted text\nLine 2\n==End-Extracted-Text=="
        result = step.extract_text_section(markdown)
        
        assert result == "This is extracted text\nLine 2"
    
    def test_extract_text_section_empty(self, excel_step_config):
        """Test text section extraction with empty markdown."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        result = step.extract_text_section("")
        assert result == ""
        
        result = step.extract_text_section("No extraction markers here")
        assert result == ""
    
    def test_extract_image_sections(self, excel_step_config):
        """Test image section extraction from markdown."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        markdown = "==Image-Descriptions==\nImage description here\nAnother line\n==End-Image-Descriptions=="
        result = step.extract_image_sections(markdown)
        
        assert result == "Image description here\nAnother line"
    
    def test_extract_image_sections_empty(self, excel_step_config):
        """Test image section extraction with empty markdown."""
        step = ExcelTextExtractorStep(excel_step_config)
        
        result = step.extract_image_sections("")
        assert result == ""
        
        result = step.extract_image_sections("No image markers here")
        assert result == ""
