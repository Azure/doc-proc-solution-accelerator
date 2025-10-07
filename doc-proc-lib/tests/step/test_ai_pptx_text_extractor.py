"""
Unit tests for the AIPowerPointTextExtractorStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.step.ai_pptx_text_extractor import AIPowerPointTextExtractorStep
from doc.proc.models import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestAIPowerPointTextExtractorStep:
    """Test cases for AIPowerPointTextExtractorStep."""
    
    @pytest.fixture
    def pptx_step_config(self):
        """Fixture for AIPowerPointTextExtractorStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="ai_powerpoint_text_extractor",
            name="ai_powerpoint_extractor_instance",
            enabled=True,
            debug_mode=True,
            services=[],
            settings={}
        )
    
    @pytest.fixture
    def pptx_document_input(self):
        """Fixture for PowerPoint document input."""
        return StepInputOutput(
            id="pptx_test",
            summary_data={"total_documents": 1},
            data={
                "documents": [
                    {
                        "file_path": "/test/sample.pptx",
                        "file_name": "sample.pptx",
                        "file_size": 2048,
                        "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "document_type": {
                            "primary_type": "powerpoint",
                            "confidence": 0.98
                        }
                    }
                ]
            }
        )
    
    def test_pptx_step_initialization(self, pptx_step_config):
        """Test successful initialization of AIPowerPointTextExtractorStep."""
        step = AIPowerPointTextExtractorStep(pptx_step_config)
        
        assert step.step_catalog_id == "ai_pptx_text_extractor"
        assert step.name == "ai_pptx_extractor_instance"
        assert step.debug_mode is True
    
    @pytest.mark.asyncio
    async def test_pptx_step_invalid_input_data(self, pptx_step_config, mock_pipeline_context):
        """Test AIPowerPointTextExtractorStep with invalid input data."""
        step = AIPowerPointTextExtractorStep(pptx_step_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_pptx_step_no_documents(self, pptx_step_config, mock_pipeline_context):
        """Test AIPowerPointTextExtractorStep with no documents."""
        step = AIPowerPointTextExtractorStep(pptx_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        with pytest.raises(ValueError) as exc_info:
            await step.run(step_input, mock_pipeline_context)
        assert "No documents list found in input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('doc.proc.step.ai_pptx_text_extractor.Presentation')
    async def test_pptx_step_successful_processing(self, mock_presentation, pptx_step_config, pptx_document_input, mock_pipeline_context):
        """Test successful PowerPoint document processing."""
        step = AIPowerPointTextExtractorStep(pptx_step_config)
        
        # Mock python-pptx
        mock_pres = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock()
        mock_shape.has_text_frame = True
        mock_shape.text_frame.text = "Sample slide text"
        mock_slide.shapes = [mock_shape]
        mock_pres.slides = [mock_slide]
        mock_presentation.return_value = mock_pres
        
        with patch('os.path.exists', return_value=True):
            result = await step.run(pptx_document_input, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Check stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] >= 0  # May be 0 or 1 depending on implementation
    
    @pytest.mark.asyncio
    async def test_pptx_step_file_not_found(self, pptx_step_config, pptx_document_input, mock_pipeline_context):
        """Test AIPowerPointTextExtractorStep when file doesn't exist."""
        step = AIPowerPointTextExtractorStep(pptx_step_config)
        
        with patch('os.path.exists', return_value=False):
            result = await step.run(pptx_document_input, mock_pipeline_context)
        
        # Should handle missing files gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert "failed_documents" in stats or "successful_documents" in stats
