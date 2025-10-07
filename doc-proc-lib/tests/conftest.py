"""
Pytest configuration and shared fixtures for doc-proc-lib tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from doc.proc.models import StepInstanceConfig, StepInputOutput
from doc.proc.service.service_base import ServiceBase
from doc.proc.pipeline.pipeline_base import PipelineExecutionContext


@pytest.fixture
def sample_step_config():
    """Fixture for creating a sample step instance configuration."""
    return StepInstanceConfig(
        step_catalog_id="test_step",
        name="test_step_instance",
        enabled=True,
        fail_pipeline_on_error=False,
        retry_on_failure=False,
        retries=3,
        timeout=600,
        fail_step_on_document_error=False,
        debug_mode=True,
        condition=None,
        services=["test_service"],
        settings={
            "test_setting": "test_value",
            "max_completion_tokens": 4000,
            "temperature": 1.0
        }
    )


@pytest.fixture
def sample_step_input():
    """Fixture for creating sample step input data."""
    return StepInputOutput(
        id="test_document_1",
        summary_data={
            "total_documents": 1,
            "processed_documents": 0
        },
        data={
            "documents": [
                {
                    "file_path": "/test/document.pdf",
                    "file_name": "document.pdf",
                    "file_size": 1024,
                    "mime_type": "application/pdf",
                    "document_type": {
                        "primary_type": "pdf",
                        "confidence": 0.95
                    }
                }
            ]
        }
    )


@pytest.fixture
def sample_empty_step_input():
    """Fixture for creating empty step input data."""
    return StepInputOutput(
        summary_data={},
        data={"documents": []}
    )


@pytest.fixture
def mock_service():
    """Fixture for creating a mock service."""
    service = MagicMock(spec=ServiceBase)
    service.name = "test_service"
    service.type = "test_type"
    service.settings = {"test_setting": "test_value"}
    service.test_connection = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_pipeline_context(mock_service):
    """Fixture for creating a mock pipeline execution context."""
    context = MagicMock(spec=PipelineExecutionContext)
    context.get_service = MagicMock(return_value=mock_service)
    context.pipeline_name = "test_pipeline"
    context.execution_id = "test_execution_123"
    return context


@pytest.fixture
def sample_service_settings():
    """Fixture for sample service settings."""
    return {
        "sample_setting": "required_value",
        "sample_optional": 20,
        "sample_with_pattern": "valid_pattern",
        "sample_enum": "option2",
        "sample_sensitive": "secret_value",
        "sample_boolean": True
    }


@pytest.fixture
def sample_document_data():
    """Fixture for sample document data."""
    return {
        "file_path": "/test/sample.pdf",
        "file_name": "sample.pdf",
        "file_size": 2048,
        "mime_type": "application/pdf",
        "document_type": {
            "primary_type": "pdf",
            "mime_type": "application/pdf",
            "confidence": 0.98,
            "category": "pdf",
            "subtype": "pdf"
        },
        "metadata": {
            "pages": 10,
            "author": "Test Author",
            "title": "Test Document",
            "created_date": "2024-01-01T00:00:00Z"
        },
        "tags": ["test", "document"]
    }


@pytest.fixture
def multiple_documents_data(sample_document_data):
    """Fixture for multiple document data."""
    documents = []
    for i in range(3):
        doc = sample_document_data.copy()
        doc["file_path"] = f"/test/sample_{i+1}.pdf"
        doc["file_name"] = f"sample_{i+1}.pdf"
        documents.append(doc)
    return documents


@pytest.fixture
def azure_ai_service_settings():
    """Fixture for Azure AI service settings."""
    return {
        "endpoint": "https://test.cognitiveservices.azure.com/openai/deployments/gpt-4.1-mini",
        "credential_type": "azure_key_credential",
        "api_key": "test_api_key",
    }


@pytest.fixture
def blob_service_settings():
    """Fixture for Azure Blob service settings."""
    return {
        "account_name": "test_account",
        "account_key": "test_key",
        "container_name": "test_container",
        "connection_string": "DefaultEndpointsProtocol=https;AccountName=test_account;AccountKey=test_key;EndpointSuffix=core.windows.net"
    }


@pytest.fixture
def ai_search_service_settings():
    """Fixture for Azure AI Search service settings."""
    return {
        "endpoint": "https://test-search.search.windows.net",
        "api_key": "test_search_key",
        "api_version": "2024-05-01-preview",
        "index_name": "test_index"
    }


@pytest.fixture
def mock_ai_inference_service():
    """Fixture for creating a mock AI inference service."""
    service = MagicMock()
    service.name = "ai_inference_service"
    service.type = "azure_ai_inference"
    
    # Mock the chat completion method
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock AI response"
    
    service.chat_completions_create = AsyncMock(return_value=mock_response)
    service.test_connection = AsyncMock(return_value=True)
    
    return service


@pytest.fixture
def mock_blob_service():
    """Fixture for creating a mock blob service."""
    service = MagicMock()
    service.name = "blob_service"
    service.type = "azure_blob"
    
    # Mock blob operations
    service.upload_blob = AsyncMock(return_value="https://test.blob.core.windows.net/container/blob.txt")
    service.download_blob = AsyncMock(return_value=b"mock blob content")
    service.list_blobs = AsyncMock(return_value=["blob1.txt", "blob2.txt"])
    service.test_connection = AsyncMock(return_value=True)
    
    return service


@pytest.fixture
def mock_ai_search_service():
    """Fixture for creating a mock AI search service."""
    service = MagicMock()
    service.name = "ai_search_service"
    service.type = "azure_ai_search"
    
    # Mock search operations
    service.write_documents = AsyncMock(return_value={"status": "success"})
    service.test_connection = AsyncMock(return_value=True)
    
    return service


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield
    # Cleanup after test
    logging.getLogger().handlers.clear()
