"""
Test Azure Content Understanding Extractor Step

This test demonstrates the basic functionality of the Azure Content Understanding
extractor step with mock data.
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

# Add the doc-proc-lib path to sys.path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from doc.proc.step.azure_content_understanding_extractor import AzureContentUnderstandingExtractorStep
from doc.proc.step.step_base import StepInstanceConfig, StepInputOutput
from doc.proc.pipeline.pipeline_base import PipelineExecutionContext


class TestAzureContentUnderstandingExtractorStep:
    """Test cases for AzureContentUnderstandingExtractorStep."""

    @pytest.fixture
    def step_config(self):
        """Create a test step configuration."""
        return StepInstanceConfig(
            step_catalog_id="azure_content_understanding_extractor",
            name="test_content_understanding_step",
            enabled=True,
            services=["test_content_understanding_service"],
            settings={
                "model_id": "prebuilt-layout",
                "extract_tables": True,
                "extract_key_value_pairs": True,
                "extract_paragraphs": True,
                "chunk_by_pages": True,
                "max_chunk_size": 4000,
                "output_format": "structured"
            }
        )

    @pytest.fixture
    def mock_service(self):
        """Create a mock Azure Content Understanding service."""
        service = MagicMock()
        service.type = 'azure_content_understanding'
        service.name = 'test_content_understanding_service'
        
        # Mock analysis result
        service.analyze_document_from_bytes = AsyncMock(return_value={
            "content": "Sample document content with tables and key-value pairs.",
            "pages": [
                {
                    "page_number": 1,
                    "words": [
                        {
                            "content": "Sample",
                            "confidence": 0.99,
                            "polygon": [0, 0, 50, 20],
                            "span": {"offset": 0, "length": 6}
                        },
                        {
                            "content": "document",
                            "confidence": 0.98,
                            "polygon": [55, 0, 120, 20],
                            "span": {"offset": 7, "length": 8}
                        }
                    ],
                    "lines": [
                        {
                            "content": "Sample document content",
                            "polygon": [0, 0, 200, 20],
                            "spans": [{"offset": 0, "length": 23}]
                        }
                    ],
                    "spans": [{"offset": 0, "length": 100}]
                }
            ],
            "tables": [
                {
                    "row_count": 2,
                    "column_count": 3,
                    "cells": [
                        {
                            "content": "Header 1",
                            "row_index": 0,
                            "column_index": 0,
                            "row_span": 1,
                            "column_span": 1,
                            "kind": "columnHeader",
                            "spans": [{"offset": 25, "length": 8}]
                        },
                        {
                            "content": "Header 2",
                            "row_index": 0,
                            "column_index": 1,
                            "row_span": 1,
                            "column_span": 1,
                            "kind": "columnHeader",
                            "spans": [{"offset": 34, "length": 8}]
                        },
                        {
                            "content": "Data 1",
                            "row_index": 1,
                            "column_index": 0,
                            "row_span": 1,
                            "column_span": 1,
                            "kind": "content",
                            "spans": [{"offset": 43, "length": 6}]
                        }
                    ],
                    "spans": [{"offset": 25, "length": 30}]
                }
            ],
            "key_value_pairs": [
                {
                    "key": {
                        "content": "Invoice Number",
                        "spans": [{"offset": 60, "length": 14}]
                    },
                    "value": {
                        "content": "INV-12345",
                        "spans": [{"offset": 75, "length": 9}]
                    },
                    "confidence": 0.95
                }
            ]
        })
        
        return service

    @pytest.fixture
    def mock_context(self, mock_service):
        """Create a mock pipeline execution context."""
        context = MagicMock(spec=PipelineExecutionContext)
        context.get_service = MagicMock(return_value=mock_service)
        return context

    @pytest.fixture
    def sample_input_data(self):
        """Create sample input data with a temporary test file."""
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as temp_file:
            # Write some dummy PDF content
            temp_file.write(b'%PDF-1.4\n%Dummy PDF content for testing\n%%EOF\n')
            temp_file_path = temp_file.name

        return StepInputOutput(
            summary_data={},
            data={
                "documents": [
                    {
                        "file_path": temp_file_path,
                        "document_type": {
                            "primary_type": "pdf"
                        }
                    }
                ]
            }
        ), temp_file_path

    def test_step_initialization(self, step_config):
        """Test successful step initialization."""
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        assert step.name == "test_content_understanding_step"
        assert step.model_id == "prebuilt-layout"
        assert step.extract_tables is True
        assert step.extract_key_value_pairs is True
        assert step.chunk_by_pages is True
        assert step.max_chunk_size == 4000
        assert step.output_format == "structured"

    def test_get_content_understanding_service(self, step_config, mock_context, mock_service):
        """Test getting the content understanding service from context."""
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        service = step.get_content_understanding_service(mock_context)
        
        assert service is not None
        assert service.type == 'azure_content_understanding'
        mock_context.get_service.assert_called()

    @pytest.mark.asyncio
    async def test_run_successful_processing(self, step_config, mock_context, sample_input_data):
        """Test successful document processing."""
        input_data, temp_file_path = sample_input_data
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        try:
            result = await step.run(input_data, mock_context)
            
            # Verify result structure
            assert isinstance(result, StepInputOutput)
            assert "test_content_understanding_step_stats" in result.summary_data
            
            # Verify statistics
            stats = result.summary_data["test_content_understanding_step_stats"]
            assert stats["total_documents"] == 1
            assert stats["successful_documents"] == 1
            assert stats["failed_documents"] == 0
            
            # Verify document chunks were added
            documents = result.data["documents"]
            assert len(documents) == 1
            assert "chunks" in documents[0]
            
            chunks = documents[0]["chunks"]
            assert len(chunks) > 0
            
            # Verify chunk structure
            chunk = chunks[0]
            assert "chunk_id" in chunk
            assert "chunk_type" in chunk
            assert "text" in chunk
            assert "confidence" in chunk
            assert chunk["input_file_path"] == temp_file_path
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @pytest.mark.asyncio
    async def test_run_with_no_documents(self, step_config, mock_context):
        """Test handling of input with no documents."""
        input_data = StepInputOutput(
            summary_data={},
            data={"documents": []}
        )
        
        step = AzureContentUnderstandingExtractorStep(step_config)
        result = await step.run(input_data, mock_context)
        
        # Verify result structure
        assert isinstance(result, StepInputOutput)
        stats = result.summary_data["test_content_understanding_step_stats"]
        assert stats["total_documents"] == 0
        assert stats["successful_documents"] == 0

    @pytest.mark.asyncio
    async def test_run_with_invalid_input(self, step_config, mock_context):
        """Test handling of invalid input data."""
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        with pytest.raises(Exception):  # Should raise StepExecutionError
            await step.run(None, mock_context)

    def test_process_analysis_results_page_chunks(self, step_config):
        """Test processing analysis results into page chunks."""
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        analysis_result = {
            "content": "Sample content",
            "pages": [
                {
                    "page_number": 1,
                    "words": [{"content": "Sample", "confidence": 0.99}],
                    "lines": [{"content": "Sample content"}]
                }
            ],
            "tables": [],
            "key_value_pairs": []
        }
        
        chunks = step._process_analysis_results(analysis_result, "/test/document.pdf")
        
        assert len(chunks) >= 1
        assert chunks[0]["chunk_type"] == "page"
        assert chunks[0]["page_num"] == 1
        assert "text" in chunks[0]

    def test_process_analysis_results_table_chunks(self, step_config):
        """Test processing analysis results with table chunks."""
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        analysis_result = {
            "content": "Sample content with table",
            "pages": [],
            "tables": [
                {
                    "row_count": 2,
                    "column_count": 2,
                    "cells": [
                        {"content": "Cell 1", "row_index": 0, "column_index": 0}
                    ]
                }
            ],
            "key_value_pairs": []
        }
        
        chunks = step._process_analysis_results(analysis_result, "/test/document.pdf")
        
        # Should have document chunk and table chunk
        table_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "table"]
        assert len(table_chunks) == 1
        assert table_chunks[0]["row_count"] == 2
        assert table_chunks[0]["column_count"] == 2

    def test_table_to_markdown_conversion(self, step_config):
        """Test table to markdown conversion."""
        config_with_markdown = step_config.copy()
        config_with_markdown.settings["output_format"] = "markdown"
        
        step = AzureContentUnderstandingExtractorStep(config_with_markdown)
        
        table_data = {
            "cells": [
                {"content": "Header 1", "row_index": 0, "column_index": 0},
                {"content": "Header 2", "row_index": 0, "column_index": 1},
                {"content": "Data 1", "row_index": 1, "column_index": 0},
                {"content": "Data 2", "row_index": 1, "column_index": 1}
            ]
        }
        
        markdown = step._table_to_markdown(table_data)
        
        assert "Header 1" in markdown
        assert "Header 2" in markdown
        assert "Data 1" in markdown
        assert "Data 2" in markdown
        assert "|" in markdown  # Markdown table format
        assert "---" in markdown  # Header separator

    def test_generate_sha1_hash(self, step_config):
        """Test SHA1 hash generation."""
        step = AzureContentUnderstandingExtractorStep(step_config)
        
        hash1 = step.generate_sha1_hash("test_string")
        hash2 = step.generate_sha1_hash("test_string")
        hash3 = step.generate_sha1_hash("different_string")
        
        # Same input should produce same hash
        assert hash1 == hash2
        # Different input should produce different hash
        assert hash1 != hash3
        # Hash should be 40 characters (SHA1 hex)
        assert len(hash1) == 40


if __name__ == "__main__":
    # Run a simple test if executed directly
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("Testing Azure Content Understanding Extractor Step...")
    
    # Create a simple test configuration
    config = StepInstanceConfig(
        step_catalog_id="azure_content_understanding_extractor",
        name="test_step",
        enabled=True,
        services=["test_service"],
        settings={
            "model_id": "prebuilt-layout",
            "extract_tables": True,
            "chunk_by_pages": True
        }
    )
    
    # Initialize step
    step = AzureContentUnderstandingExtractorStep(config)
    print(f"✓ Step initialized successfully: {step.name}")
    print(f"✓ Model ID: {step.model_id}")
    print(f"✓ Extract tables: {step.extract_tables}")
    
    # Test hash generation
    hash_result = step.generate_sha1_hash("test_document_page_1")
    print(f"✓ SHA1 hash generated: {hash_result}")
    
    print("Basic tests completed successfully!")
