"""
Unit tests for the AzureAIInferenceService class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.service.azure_ai_inference_service import AzureAIInferenceService
from doc.proc.service.service_base import ServiceExecutionError


class TestAzureAIInferenceService:
    """Test cases for AzureAIInferenceService."""
    
    def test_azure_ai_inference_service_initialization_success(self, azure_ai_service_settings):
        """Test successful AzureAIInferenceService initialization."""
        service = AzureAIInferenceService(
            name="test_ai_service",
            type="azure_ai_inference",
            settings=azure_ai_service_settings
        )
        
        assert service.name == "test_ai_service"
        assert service.type == "azure_ai_inference"
        assert service.endpoint == "https://test.cognitiveservices.azure.com/openai/deployments/gpt-4.1-mini"
        assert service.api_key == "test_api_key"
        assert service.credential_type == "azure_key_credential"

    
    def test_azure_ai_inference_service_missing_endpoint(self):
        """Test AzureAIInferenceService initialization with missing endpoint."""
        invalid_settings = {
            "api_key": "test_api_key"
            # Missing endpoint
        }
        
        with pytest.raises(ValueError) as exc_info:
            AzureAIInferenceService(
                name="test_service",
                type="azure_ai_inference",
                settings=invalid_settings
            )
        
        assert "endpoint" in str(exc_info.value).lower()
    
    def test_azure_ai_inference_service_missing_api_key(self):
        """Test AzureAIInferenceService initialization with missing API key."""
        invalid_settings = {
            "endpoint": "https://test.openai.azure.com/",
            "credential_type": "azure_key_credential",
            # Missing api_key
        }
        
        with pytest.raises(ValueError) as exc_info:
            AzureAIInferenceService(
                name="test_service",
                type="azure_ai_inference",
                settings=invalid_settings
            )
        
        assert "api_key" in str(exc_info.value).lower()
    
    
    @pytest.mark.asyncio
    @patch('doc.proc.service.azure_ai_inference_service.ChatCompletionsClient')
    async def test_azure_ai_inference_service_test_connection_success(self, mock_client_class, azure_ai_service_settings):
        """Test successful connection test."""
        # Mock the client and its methods
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock a successful completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.complete = AsyncMock(return_value=mock_response)
        
        service = AzureAIInferenceService(
            name="test_service",
            type="azure_ai_inference",
            settings=azure_ai_service_settings
        )
        
        result = await service.test_connection()
        assert result is True
    
    @pytest.mark.asyncio
    @patch('doc.proc.service.azure_ai_inference_service.ChatCompletionsClient')
    async def test_azure_ai_inference_service_test_connection_failure(self, mock_client_class, azure_ai_service_settings):
        """Test connection test failure."""
        # Mock the client to raise an exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.complete = AsyncMock(side_effect=ServiceExecutionError)
        
        service = AzureAIInferenceService(
            name="test_service",
            type="azure_ai_inference",
            settings=azure_ai_service_settings
        )

        with pytest.raises(ServiceExecutionError) as exc_info:
            await service.test_connection()

        assert "Failed to connect to Azure AI Inference Service" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('doc.proc.service.azure_ai_inference_service.ChatCompletionsClient')
    async def test_azure_ai_inference_service_chat_completion(self, mock_client_class, azure_ai_service_settings):
        """Test chat completion functionality."""
        # Mock the client and its methods
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock a successful completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI response"
        mock_client.complete = AsyncMock(return_value=mock_response)
        
        service = AzureAIInferenceService(
            name="test_service",
            type="azure_ai_inference",
            settings=azure_ai_service_settings
        )
        
        # Test that the service has a client after initialization
        assert hasattr(service, 'chat_completions_client')
    
    def test_azure_ai_inference_service_settings_validation(self):
        """Test that all required settings are validated."""
        # Test with completely empty settings
        with pytest.raises(ValueError):
            AzureAIInferenceService(
                name="test_service",
                type="azure_ai_inference",
                settings={}
            )
        
        # Test with empty strings
        invalid_settings = {
            "endpoint": "",
            "credential_type": "",
            "api_key": "",
        }
        
        with pytest.raises(ValueError):
            AzureAIInferenceService(
                name="test_service",
                type="azure_ai_inference",
                settings=invalid_settings
            )
    
    def test_azure_ai_inference_service_inheritance(self, azure_ai_service_settings):
        """Test that AzureAIInferenceService properly inherits from ServiceBase."""
        service = AzureAIInferenceService(
            name="test_service",
            type="azure_ai_inference",
            settings=azure_ai_service_settings
        )
        
        # Should have inherited attributes from ServiceBase
        assert hasattr(service, 'name')
        assert hasattr(service, 'type')
        assert hasattr(service, 'settings')
        assert hasattr(service, 'params')
        
        # Should have the test_connection method
        assert hasattr(service, 'test_connection')
        assert callable(service.test_connection)
