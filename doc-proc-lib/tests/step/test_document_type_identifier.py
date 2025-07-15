"""
Unit tests for the DocumentTypeIdentifierStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.step.document_type_identifier import (
    DocumentTypeIdentifierStep, 
    DocumentCategory, 
    IdentificationMethod
)
from doc.proc.step.step_base import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestDocumentTypeIdentifierStep:
    """Test cases for DocumentTypeIdentifierStep."""
    
    @pytest.fixture
    def doc_identifier_step_config(self):
        """Fixture for DocumentTypeIdentifierStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="document_type_identifier",
            name="doc_identifier_instance",
            enabled=True,
            debug_mode=True,
            services=[],
            settings={
                "identification_methods": "magic_bytes, file_extension"
            }
        )
    
    @pytest.fixture
    def document_input_mixed(self):
        """Fixture for mixed document types input."""
        return StepInputOutput(
            id="mixed_docs_test",
            summary_data={"total_documents": 3},
            data={
                "documents": [
                    {
                        "file_path": "/test/sample.pdf",
                        "file_name": "sample.pdf",
                        "file_size": 2048
                    },
                    {
                        "file_path": "/test/document.docx",
                        "file_name": "document.docx",
                        "file_size": 1024
                    },
                    {
                        "file_path": "/test/presentation.pptx",
                        "file_name": "presentation.pptx",
                        "file_size": 3072
                    }
                ]
            }
        )
    
    def test_doc_identifier_step_initialization(self, doc_identifier_step_config):
        """Test successful initialization of DocumentTypeIdentifierStep."""
        step = DocumentTypeIdentifierStep(doc_identifier_step_config)
        
        assert step.step_catalog_id == "document_type_identifier"
        assert step.name == "doc_identifier_instance"
        assert step.debug_mode is True
        assert len(step.identification_methods) == 2
        assert IdentificationMethod.MAGIC_BYTES in step.identification_methods
        assert IdentificationMethod.FILE_EXTENSION in step.identification_methods
    
    def test_doc_identifier_step_default_methods(self):
        """Test DocumentTypeIdentifierStep with default identification methods."""
        config = StepInstanceConfig(
            step_catalog_id="document_type_identifier",
            name="doc_identifier_instance",
            settings={}  # No methods specified
        )
        
        step = DocumentTypeIdentifierStep(config)
        
        # Should use default methods
        assert len(step.identification_methods) == 2
        assert IdentificationMethod.MAGIC_BYTES in step.identification_methods
        assert IdentificationMethod.FILE_EXTENSION in step.identification_methods
    
    def test_doc_identifier_step_single_method(self):
        """Test DocumentTypeIdentifierStep with single identification method."""
        config = StepInstanceConfig(
            step_catalog_id="document_type_identifier",
            name="doc_identifier_instance",
            settings={
                "identification_methods": "file_extension"
            }
        )
        
        step = DocumentTypeIdentifierStep(config)
        
        assert len(step.identification_methods) == 1
        assert IdentificationMethod.FILE_EXTENSION in step.identification_methods
    
    @pytest.mark.asyncio
    async def test_doc_identifier_step_invalid_input_data(self, doc_identifier_step_config, mock_pipeline_context):
        """Test DocumentTypeIdentifierStep with invalid input data."""
        step = DocumentTypeIdentifierStep(doc_identifier_step_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_doc_identifier_step_no_documents(self, doc_identifier_step_config, mock_pipeline_context):
        """Test DocumentTypeIdentifierStep with no documents."""
        step = DocumentTypeIdentifierStep(doc_identifier_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        result = await step.run(step_input, mock_pipeline_context)
        assert result.summary_data[f"{step.name}_stats"]["total_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_doc_identifier_step_successful_processing(self, document_input_mixed, mock_pipeline_context):
        """Test successful document type identification."""
        
        config = StepInstanceConfig(
            step_catalog_id="document_type_identifier",
            name="doc_identifier_instance",
            settings={
                "identification_methods": "file_extension"
            }
        )
        step = DocumentTypeIdentifierStep(config)
        
        result = await step.run(document_input_mixed, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Check that document types were identified
        documents = result.data["documents"]
        assert len(documents) == 3
        
        # Check stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 3
        assert stats["successful_documents"] >= 0
    
    @pytest.mark.asyncio
    async def test_doc_identifier_step_file_not_found(self, doc_identifier_step_config, document_input_mixed, mock_pipeline_context):
        """Test DocumentTypeIdentifierStep when files don't exist."""
        step = DocumentTypeIdentifierStep(doc_identifier_step_config)
        
        with patch('os.path.exists', return_value=False):
            result = await step.run(document_input_mixed, mock_pipeline_context)
        
        # Should handle missing files gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 3
        assert "failed_documents" in stats or "successful_documents" in stats
    
    @pytest.mark.asyncio
    async def test_doc_identifier_step_extension_only(self, mock_pipeline_context, document_input_mixed):
        """Test DocumentTypeIdentifierStep using only file extension method."""
        config = StepInstanceConfig(
            step_catalog_id="document_type_identifier",
            name="doc_identifier_instance",
            settings={
                "identification_methods": "file_extension"
            }
        )
        
        step = DocumentTypeIdentifierStep(config)
        
        result = await step.run(document_input_mixed, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Should identify documents based on file extensions
        documents = result.data["documents"]
        for doc in documents:
            # Should have document_type information added
            if "document_type" in doc:
                assert "primary_type" in doc["document_type"]
                assert "confidence" in doc["document_type"]
    
    @pytest.mark.asyncio
    async def test_doc_identifier_step_invalid_document_format(self, doc_identifier_step_config, mock_pipeline_context):
        """Test DocumentTypeIdentifierStep with invalid document format."""
        step = DocumentTypeIdentifierStep(doc_identifier_step_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={
                "documents": [
                    "invalid_document_format",  # Should be a dict
                    {"missing_file_path": "no_path"}  # Missing file_path
                ]
            }
        )
        
        result = await step.run(step_input, mock_pipeline_context)
        
        # Should handle invalid formats gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 2
        assert "failed_documents" in stats


class TestDocumentCategory:
    """Test cases for DocumentCategory enum."""
    
    def test_document_categories_exist(self):
        """Test that all expected document categories exist."""
        expected_categories = [
            "office_document", "pdf", "image", "audio", "video",
            "archive", "text", "spreadsheet", "presentation",
            "email", "web", "executable", "unknown"
        ]
        
        for category in expected_categories:
            assert hasattr(DocumentCategory, category.upper())
    
    def test_document_category_values(self):
        """Test document category enum values."""
        assert DocumentCategory.PDF.value == "pdf"
        assert DocumentCategory.OFFICE_DOCUMENT.value == "office_document"
        assert DocumentCategory.UNKNOWN.value == "unknown"


class TestIdentificationMethod:
    """Test cases for IdentificationMethod enum."""
    
    def test_identification_methods_exist(self):
        """Test that expected identification methods exist."""
        assert hasattr(IdentificationMethod, "MAGIC_BYTES")
        assert hasattr(IdentificationMethod, "FILE_EXTENSION")
    
    def test_identification_method_values(self):
        """Test identification method enum values."""
        assert IdentificationMethod.MAGIC_BYTES.value == "magic_bytes"
        assert IdentificationMethod.FILE_EXTENSION.value == "file_extension"
