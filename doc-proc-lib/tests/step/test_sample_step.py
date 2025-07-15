"""
Unit tests for the SampleStep class.
"""

import pytest
from unittest.mock import AsyncMock
from doc.proc.step.sample import SampleStep
from doc.proc.step.step_base import StepInputOutput, StepExecutionError


class TestSampleStep:
    """Test cases for SampleStep."""
    
    @pytest.mark.asyncio
    async def test_sample_step_run_success(self, sample_step_config, sample_step_input, mock_pipeline_context):
        """Test successful execution of SampleStep."""
        step = SampleStep(sample_step_config)
        
        result = await step.run(sample_step_input, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        assert f"{step.name}_stats" in result.summary_data
        
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
        assert stats["successful_documents"] == 1
        assert stats["failed_documents"] == 0
        
        # Check that sample data was added to the document
        documents = result.data["documents"]
        assert len(documents) == 1
        assert "sample_data" in documents[0]
        assert documents[0]["sample_data"]["sample_key"] == "sample_value"
        assert documents[0]["sample_data"]["sample_summary"] == "This is a sample summary"
        assert documents[0]["sample_data"]["sample_data"] == "This is sample data"
    
    @pytest.mark.asyncio
    async def test_sample_step_with_multiple_documents(self, sample_step_config, mock_pipeline_context, multiple_documents_data):
        """Test SampleStep with multiple documents."""
        step_input = StepInputOutput(
            summary_data={"total_documents": len(multiple_documents_data)},
            data={"documents": multiple_documents_data}
        )
        
        step = SampleStep(sample_step_config)
        result = await step.run(step_input, mock_pipeline_context)
        
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 3
        assert stats["successful_documents"] == 3
        assert stats["failed_documents"] == 0

        # Check that all documents have sample data
        for doc in result.data["documents"]:
            assert "sample_data" in doc
            assert doc["sample_data"]["sample_key"] == "sample_value"
    
    @pytest.mark.asyncio
    async def test_sample_step_with_empty_documents(self, sample_step_config, sample_empty_step_input, mock_pipeline_context):
        """Test SampleStep with empty documents list."""
        step = SampleStep(sample_step_config)
        
        result = await step.run(sample_empty_step_input, mock_pipeline_context)
        
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 0
        assert stats["successful_documents"] == 0
        assert stats["failed_documents"] == 0

    @pytest.mark.asyncio
    async def test_sample_step_no_documents_key(self, sample_step_config, mock_pipeline_context):
        """Test SampleStep when input data has no documents key."""
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents key
        )
        
        step = SampleStep(sample_step_config)
        
        result = await step.run(step_input, mock_pipeline_context)
        
        assert result.summary_data[f"{step.name}_stats"]["total_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["successful_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["failed_documents"] == 0

    @pytest.mark.asyncio
    async def test_sample_step_documents_not_list(self, sample_step_config, mock_pipeline_context):
        """Test SampleStep when documents is not a list."""
        step_input = StepInputOutput(
            summary_data={},
            data={"documents": "not_a_list"}
        )
        
        step = SampleStep(sample_step_config)
        
        result = await step.run(step_input, mock_pipeline_context)
        
        assert result.summary_data[f"{step.name}_stats"]["total_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["successful_documents"] == 0
        assert result.summary_data[f"{step.name}_stats"]["failed_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_sample_step_preserves_original_summary_data(self, sample_step_config, mock_pipeline_context):
        """Test that SampleStep preserves original summary data."""
        original_summary = {
            "pipeline_start_time": "2024-01-01T00:00:00Z",
            "total_files": 5
        }
        
        step_input = StepInputOutput(
            summary_data=original_summary,
            data={"documents": [{"file_path": "/test/doc.pdf"}]}
        )
        
        step = SampleStep(sample_step_config)
        result = await step.run(step_input, mock_pipeline_context)
        
        # Check that original summary data is preserved
        assert result.summary_data["pipeline_start_time"] == "2024-01-01T00:00:00Z"
        assert result.summary_data["total_files"] == 5
        
        # Check that new stats are added
        assert f"{step.name}_stats" in result.summary_data
    
    @pytest.mark.asyncio
    async def test_sample_step_preserves_original_data(self, sample_step_config, mock_pipeline_context):
        """Test that SampleStep preserves original data structure."""
        original_data = {
            "documents": [{"file_path": "/test/doc.pdf", "existing_field": "existing_value"}],
            "metadata": {"pipeline_id": "test_123"},
            "other_field": "other_value"
        }
        
        step_input = StepInputOutput(
            summary_data={},
            data=original_data
        )
        
        step = SampleStep(sample_step_config)
        result = await step.run(step_input, mock_pipeline_context)
        
        # Check that original data is preserved
        assert result.data["metadata"]["pipeline_id"] == "test_123"
        assert result.data["other_field"] == "other_value"
        
        # Check that existing document fields are preserved
        doc = result.data["documents"][0]
        assert doc["file_path"] == "/test/doc.pdf"
        assert doc["existing_field"] == "existing_value"
        
        # Check that sample data was added
        assert "sample_data" in doc
