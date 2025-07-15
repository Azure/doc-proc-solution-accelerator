"""
Unit tests for the AISearchIndexWriterStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.step.ai_search_index_writer import AISearchIndexWriterStep
from doc.proc.step.step_base import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestAISearchIndexWriterStep:
    """Test cases for AISearchIndexWriterStep."""
    
    @pytest.fixture
    def ai_search_step_config(self):
        """Fixture for AISearchIndexWriterStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="ai_search_index_writer",
            name="ai_search_writer_instance",
            enabled=True,
            debug_mode=True,
            services=["ai_search_service"],
            settings={
                "index_name": "test_index",
                "batch_size": 10,
                "merge_or_upload": "upload"
            }
        )
    
    @pytest.fixture
    def search_documents_input(self):
        """Fixture for documents ready for search indexing."""
        return StepInputOutput(
            id="search_test",
            summary_data={"total_documents": 2},
            data={
                "documents": [
                    {
                        "file_path": "/test/doc1.pdf",
                        "file_name": "doc1.pdf",
                        "content": "Sample document content for indexing",
                        "metadata": {
                            "title": "Document 1",
                            "author": "Test Author"
                        },
                        "id": "doc_1"
                    },
                    {
                        "file_path": "/test/doc2.pdf",
                        "file_name": "doc2.pdf",
                        "content": "Another document with searchable content",
                        "metadata": {
                            "title": "Document 2",
                            "author": "Test Author 2"
                        },
                        "id": "doc_2"
                    }
                ]
            }
        )
    
    def test_ai_search_step_initialization(self, ai_search_step_config):
        """Test successful initialization of AISearchIndexWriterStep."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        assert step.step_catalog_id == "ai_search_index_writer"
        assert step.name == "ai_search_writer_instance"
        assert step.debug_mode is True
        assert "ai_search_service" in step.services
    
    @pytest.mark.asyncio
    async def test_ai_search_step_invalid_input_data(self, ai_search_step_config, mock_pipeline_context):
        """Test AISearchIndexWriterStep with invalid input data."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ai_search_step_no_documents(self, ai_search_step_config, mock_pipeline_context):
        """Test AISearchIndexWriterStep with no documents."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        with pytest.raises(ValueError) as exc_info:
            await step.run(step_input, mock_pipeline_context)
        assert "No documents list found in input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ai_search_step_no_search_service(self, ai_search_step_config, search_documents_input):
        """Test AISearchIndexWriterStep when search service is not available."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        # Mock context with no search service
        mock_context = MagicMock()
        mock_context.get_service.return_value = None
        
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(search_documents_input, mock_context)
        assert "AI Search Service not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ai_search_step_successful_indexing(self, ai_search_step_config, search_documents_input, mock_ai_search_service):
        """Test successful document indexing."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        # Mock context with search service
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_search_service
        
        result = await step.run(search_documents_input, mock_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Check that indexing service was called
        mock_ai_search_service.index_document.assert_called()
        
        # Check stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 2
        assert "successful_documents" in stats or "indexed_documents" in stats
    
    @pytest.mark.asyncio
    async def test_ai_search_step_with_empty_documents(self, ai_search_step_config, sample_empty_step_input, mock_ai_search_service):
        """Test AISearchIndexWriterStep with empty documents list."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_search_service
        
        result = await step.run(sample_empty_step_input, mock_context)
        
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_ai_search_step_batch_processing(self, search_documents_input, mock_ai_search_service):
        """Test batch processing with custom batch size."""
        config = StepInstanceConfig(
            step_catalog_id="ai_search_index_writer",
            name="ai_search_writer_instance",
            services=["ai_search_service"],
            settings={
                "index_name": "test_index",
                "batch_size": 1  # Small batch size for testing
            }
        )
        
        step = AISearchIndexWriterStep(config)
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_search_service
        
        result = await step.run(search_documents_input, mock_context)
        
        # Should process documents in batches
        assert isinstance(result, StepInputOutput)
        mock_ai_search_service.index_document.assert_called()
    
    @pytest.mark.asyncio
    async def test_ai_search_step_indexing_failure(self, ai_search_step_config, search_documents_input):
        """Test handling of indexing failures."""
        step = AISearchIndexWriterStep(ai_search_step_config)
        
        # Mock search service that fails
        mock_service = MagicMock()
        mock_service.index_document = AsyncMock(side_effect=Exception("Indexing failed"))
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_service
        
        result = await step.run(search_documents_input, mock_context)
        
        # Should handle failures gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 2
        assert "failed_documents" in stats
