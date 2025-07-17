"""
Unit tests for the PDFTextExtractorStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.step.pdf_text_extractor import PDFTextExtractorStep
from doc.proc.step.step_base import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestPDFTextExtractorStep:
    """Test cases for PDFTextExtractorStep."""
    
    @pytest.fixture
    def pdf_step_config(self):
        """Fixture for PDFTextExtractorStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="pdf_text_extractor",
            name="pdf_extractor_instance",
            enabled=True,
            debug_mode=True,
            services=["ai_inference_service"],
            settings={
                "png_output_folder": "test_output_pngs",
                "num_pages": 5,
                "prompts": {
                    "system": "You are a helpful assistant that extracts text from images.",
                    "user": "Extract the text from this image and return it as structured data."
                },
                "max_completion_tokens": 4000,
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }
        )
    
    @pytest.fixture
    def pdf_document_input(self):
        """Fixture for PDF document input."""
        return StepInputOutput(
            id="pdf_test",
            summary_data={"total_documents": 1},
            data={
                "documents": [
                    {
                        "file_path": "/test/sample.pdf",
                        "file_name": "sample.pdf",
                        "file_size": 2048,
                        "mime_type": "application/pdf",
                        "document_type": {
                            "primary_type": "pdf",
                            "confidence": 0.98
                        }
                    }
                ]
            }
        )
    
    def test_pdf_step_initialization_success(self, pdf_step_config):
        """Test successful initialization of PDFTextExtractorStep."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        assert step.png_output_folder == "test_output_pngs"
        assert step.pages_to_convert == 5
        assert step.system_prompt == "You are a helpful assistant that extracts text from images."
        assert step.user_prompt == "Extract the text from this image and return it as structured data."
        assert step.max_completion_tokens == 4000
        assert step.temperature == 0.7
        assert step.top_p == 0.9
        assert step.frequency_penalty == 0.1
        assert step.presence_penalty == 0.1
    
    def test_pdf_step_initialization_missing_prompts(self):
        """Test PDFTextExtractorStep initialization with missing prompts."""
        config = StepInstanceConfig(
            step_catalog_id="pdf_text_extractor",
            name="pdf_extractor_instance",
            settings={}  # Missing prompts
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            PDFTextExtractorStep(config)
        
        assert "No prompts found in settings" in str(exc_info.value)
    
    def test_pdf_step_initialization_missing_system_prompt(self):
        """Test PDFTextExtractorStep initialization with missing system prompt."""
        config = StepInstanceConfig(
            step_catalog_id="pdf_text_extractor",
            name="pdf_extractor_instance",
            settings={
                "prompts": {
                    "user": "Extract text from image"
                    # Missing system prompt
                }
            }
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            PDFTextExtractorStep(config)
        
        assert "System prompt not found in settings" in str(exc_info.value)
    
    def test_pdf_step_initialization_missing_user_prompt(self):
        """Test PDFTextExtractorStep initialization with missing user prompt."""
        config = StepInstanceConfig(
            step_catalog_id="pdf_text_extractor",
            name="pdf_extractor_instance",
            settings={
                "prompts": {
                    "system": "You are a helpful assistant"
                    # Missing user prompt
                }
            }
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            PDFTextExtractorStep(config)
        
        assert "User prompt not found in settings" in str(exc_info.value)
    
    def test_pdf_step_initialization_default_values(self):
        """Test PDFTextExtractorStep initialization with default values."""
        config = StepInstanceConfig(
            step_catalog_id="pdf_text_extractor",
            name="pdf_extractor_instance",
            settings={
                "prompts": {
                    "system": "System prompt",
                    "user": "User prompt"
                }
                # Other settings will use defaults
            }
        )
        
        step = PDFTextExtractorStep(config)
        
        assert step.png_output_folder == "output_pngs"  # Default value
        assert step.pages_to_convert == -1  # Default value (all pages)
        assert step.max_completion_tokens == 4000  # Default value
        assert step.temperature == 1.0  # Default value
        assert step.top_p == 1.0  # Default value
        assert step.frequency_penalty == 0.0  # Default value
        assert step.presence_penalty == 0.0  # Default value
    
    @pytest.mark.asyncio
    async def test_pdf_step_invalid_input_data(self, pdf_step_config, mock_pipeline_context):
        """Test PDFTextExtractorStep with invalid input data."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
        
        # Test with invalid type
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run("invalid", mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
        
        # Test with missing data attribute
        invalid_input = StepInputOutput()
        invalid_input.data = None
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(invalid_input, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_pdf_step_no_documents(self, pdf_step_config, mock_ai_inference_service):
        """Test PDFTextExtractorStep with no documents."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_inference_service

        result = await step.run(step_input, mock_context)
        assert result.summary_data[f"{step.name}_stats"]["total_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["failed_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["successful_documents"] == 0

    @pytest.mark.asyncio
    async def test_pdf_step_documents_not_list(self, pdf_step_config, mock_ai_inference_service):
        """Test PDFTextExtractorStep when documents is not a list."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={"documents": "not_a_list"}
        )
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_inference_service

        result = await step.run(step_input, mock_context)
        assert result.summary_data[f"{step.name}_stats"]["total_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["failed_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["successful_documents"] == 0

    @pytest.mark.asyncio
    async def test_pdf_step_no_ai_service(self, pdf_step_config, pdf_document_input):
        """Test PDFTextExtractorStep when AI service is not available."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        # Mock context with no AI service
        mock_context = MagicMock()
        mock_context.get_service.return_value = None
        
        with patch.object(step, 'get_ai_inference_service', return_value=None):
            with pytest.raises(StepExecutionError) as exc_info:
                await step.run(pdf_document_input, mock_context)
            assert "Azure AI Model Inference Service not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_pdf_step_invalid_document_format(self, pdf_step_config, mock_pipeline_context):
        """Test PDFTextExtractorStep with invalid document format."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={
                "documents": [
                    "invalid_document_format"  # Should be a dict with file_path
                ]
            }
        )
        
        # Mock the AI service
        mock_ai_service = MagicMock()
        with patch.object(step, 'get_ai_inference_service', return_value=mock_ai_service):
            result = await step.run(step_input, mock_pipeline_context)
            
            # Check that stats show failed document
            stats = result.summary_data[f"{step.name}_stats"]
            assert stats["total_documents"] == 1
            assert stats["failed_documents"] == 1
            assert stats["successful_documents"] == 0
    
    @pytest.mark.asyncio
    @patch('doc.proc.step.pdf_text_extractor.pymupdf')
    async def test_pdf_step_successful_processing(self, mock_pymupdf, pdf_step_config, pdf_document_input, mock_ai_inference_service):
        """Test successful PDF processing."""
        step = PDFTextExtractorStep(pdf_step_config)
        
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.pil_save.return_value = None
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_pymupdf.open.return_value = mock_doc
        
        # Mock context and AI service
        mock_context = MagicMock()
        
        with patch.object(step, 'get_ai_inference_service', return_value=mock_ai_inference_service):
            with patch('os.path.exists', return_value=True):
                with patch('os.makedirs'):
                    result = await step.run(pdf_document_input, mock_context)
        
        assert isinstance(result, StepInputOutput)
        # The method should complete without errors
        assert result is not None
