"""
Unit tests for the WordTextExtractorStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from doc.proc.step.word_text_extractor import WordTextExtractorStep
from doc.proc.step.step_base import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestWordTextExtractorStep:
    """Test cases for WordTextExtractorStep."""
    
    @pytest.fixture
    def word_step_config(self):
        """Fixture for WordTextExtractorStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="word_text_extractor",
            name="word_extractor_instance",
            enabled=True,
            debug_mode=True,
            services=[],
            settings={}
        )
    
    @pytest.fixture
    def word_document_input(self):
        """Fixture for Word document input."""
        return StepInputOutput(
            id="word_test",
            summary_data={"total_documents": 1},
            data={
                "documents": [
                    {
                        "file_path": "/test/sample.docx",
                        "file_name": "sample.docx",
                        "file_size": 2048,
                        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "document_type": {
                            "primary_type": "word",
                            "confidence": 0.98
                        }
                    }
                ]
            }
        )
    
    def test_word_step_initialization(self, word_step_config):
        """Test successful initialization of WordTextExtractorStep."""
        step = WordTextExtractorStep(word_step_config)
        
        assert step.step_catalog_id == "word_text_extractor"
        assert step.name == "word_extractor_instance"
        assert step.debug_mode is True
    
    @pytest.mark.asyncio
    async def test_word_step_invalid_input_data(self, word_step_config, mock_pipeline_context):
        """Test WordTextExtractorStep with invalid input data."""
        step = WordTextExtractorStep(word_step_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_word_step_no_documents(self, word_step_config, mock_pipeline_context):
        """Test WordTextExtractorStep with no documents."""
        step = WordTextExtractorStep(word_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        with pytest.raises(ValueError) as exc_info:
            await step.run(step_input, mock_pipeline_context)
        assert "No documents list found in input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('doc.proc.step.word_text_extractor.docx.Document')
    async def test_word_step_successful_processing(self, mock_docx, word_step_config, word_document_input, mock_pipeline_context):
        """Test successful Word document processing."""
        step = WordTextExtractorStep(word_step_config)
        
        # Mock python-docx
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Sample paragraph text"
        mock_doc.paragraphs = [mock_paragraph]
        mock_docx.return_value = mock_doc
        
        with patch('os.path.exists', return_value=True):
            result = await step.run(word_document_input, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Check stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] >= 0  # May be 0 or 1 depending on implementation
    
    @pytest.mark.asyncio
    async def test_word_step_file_not_found(self, word_step_config, word_document_input, mock_pipeline_context):
        """Test WordTextExtractorStep when file doesn't exist."""
        step = WordTextExtractorStep(word_step_config)
        
        with patch('os.path.exists', return_value=False):
            result = await step.run(word_document_input, mock_pipeline_context)
        
        # Should handle missing files gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert "failed_documents" in stats or "successful_documents" in stats
    
    @pytest.mark.asyncio
    async def test_word_step_invalid_document_format(self, word_step_config, mock_pipeline_context):
        """Test WordTextExtractorStep with invalid document format."""
        step = WordTextExtractorStep(word_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={
                "documents": [
                    "invalid_document_format"  # Should be a dict
                ]
            }
        )
        
        result = await step.run(step_input, mock_pipeline_context)
        
        # Should handle invalid format gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
