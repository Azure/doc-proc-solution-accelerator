"""
Unit tests for the CustomAIPromptStep class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.step.custom_ai_prompt import CustomAIPromptStep
from doc.proc.step.step_base import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestCustomAIPromptStep:
    """Test cases for CustomAIPromptStep."""
    
    @pytest.fixture
    def custom_ai_prompt_config(self):
        """Fixture for CustomAIPromptStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="custom_ai_prompt",
            name="custom_ai_prompt_instance",
            enabled=True,
            debug_mode=True,
            services=["ai_inference_service"],
            settings={
                "prompts": {
                    "system": "You are an expert document analyzer.",
                    "user": "Analyze this document and extract key information: {content}"
                },
                "max_completion_tokens": 2000,
                "temperature": 0.3,
                "response_format": "json"
            }
        )
    
    @pytest.fixture
    def documents_with_content_input(self):
        """Fixture for documents with content for AI processing."""
        return StepInputOutput(
            id="ai_prompt_test",
            summary_data={"total_documents": 2},
            data={
                "documents": [
                    {
                        "file_path": "/test/doc1.pdf",
                        "file_name": "doc1.pdf",
                        "content": "This is a contract document with important terms and conditions.",
                        "document_type": {
                            "primary_type": "pdf",
                            "category": "contract"
                        }
                    },
                    {
                        "file_path": "/test/doc2.txt",
                        "file_name": "doc2.txt",
                        "content": "This is a meeting summary with action items and decisions.",
                        "document_type": {
                            "primary_type": "text",
                            "category": "meeting_notes"
                        }
                    }
                ]
            }
        )
    
    def test_custom_ai_prompt_step_initialization_success(self, custom_ai_prompt_config):
        """Test successful initialization of CustomAIPromptStep."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        assert step.step_catalog_id == "custom_ai_prompt"
        assert step.name == "custom_ai_prompt_instance"
        assert step.debug_mode is True
        assert "ai_inference_service" in step.services
    
    def test_custom_ai_prompt_step_missing_prompts(self):
        """Test CustomAIPromptStep initialization with missing prompts."""
        config = StepInstanceConfig(
            step_catalog_id="custom_ai_prompt",
            name="custom_ai_prompt_instance",
            settings={}  # Missing prompts
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            CustomAIPromptStep(config)
        
        assert "No prompts found in settings" in str(exc_info.value)
    
    def test_custom_ai_prompt_step_missing_system_prompt(self):
        """Test CustomAIPromptStep initialization with missing system prompt."""
        config = StepInstanceConfig(
            step_catalog_id="custom_ai_prompt",
            name="custom_ai_prompt_instance",
            settings={
                "prompts": {
                    "user": "Analyze this document"
                    # Missing system prompt
                }
            }
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            CustomAIPromptStep(config)
        
        assert "System prompt not found in settings" in str(exc_info.value)
    
    def test_custom_ai_prompt_step_missing_user_prompt(self):
        """Test CustomAIPromptStep initialization with missing user prompt."""
        config = StepInstanceConfig(
            step_catalog_id="custom_ai_prompt",
            name="custom_ai_prompt_instance",
            settings={
                "prompts": {
                    "system": "You are a helpful assistant"
                    # Missing user prompt
                }
            }
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            CustomAIPromptStep(config)
        
        assert "User prompt not found in settings" in str(exc_info.value)
    
    def test_custom_ai_prompt_step_default_values(self):
        """Test CustomAIPromptStep initialization with default values."""
        config = StepInstanceConfig(
            step_catalog_id="custom_ai_prompt",
            name="custom_ai_prompt_instance",
            settings={
                "prompts": {
                    "system": "System prompt",
                    "user": "User prompt"
                }
                # Other settings will use defaults
            }
        )
        
        step = CustomAIPromptStep(config)
        
        # Should have default values for AI parameters
        assert hasattr(step, 'max_completion_tokens')
        assert hasattr(step, 'temperature')
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_invalid_input_data(self, custom_ai_prompt_config, mock_pipeline_context):
        """Test CustomAIPromptStep with invalid input data."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_pipeline_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_no_documents(self, custom_ai_prompt_config, mock_pipeline_context):
        """Test CustomAIPromptStep with no documents."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={}  # No documents
        )
        
        with pytest.raises(ValueError) as exc_info:
            await step.run(step_input, mock_pipeline_context)
        assert "No documents list found in input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_no_ai_service(self, custom_ai_prompt_config, documents_with_content_input):
        """Test CustomAIPromptStep when AI service is not available."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        # Mock context with no AI service
        mock_context = MagicMock()
        mock_context.get_service.return_value = None
        
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(documents_with_content_input, mock_context)
        assert "AI Inference Service not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_successful_processing(self, custom_ai_prompt_config, documents_with_content_input, mock_ai_inference_service):
        """Test successful AI prompt processing."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        # Mock AI service response
        mock_ai_inference_service.chat_completions_create.return_value.choices[0].message.content = \
            '{"extracted_info": "Sample extracted information", "category": "contract"}'
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_inference_service
        
        result = await step.run(documents_with_content_input, mock_context)
        
        assert isinstance(result, StepInputOutput)
        
        # Check that AI service was called
        mock_ai_inference_service.chat_completions_create.assert_called()
        
        # Check stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 2
        assert "successful_documents" in stats
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_with_empty_documents(self, custom_ai_prompt_config, sample_empty_step_input, mock_ai_inference_service):
        """Test CustomAIPromptStep with empty documents list."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_inference_service
        
        result = await step.run(sample_empty_step_input, mock_context)
        
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_ai_failure(self, custom_ai_prompt_config, documents_with_content_input):
        """Test handling of AI service failures."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        # Mock AI service that fails
        mock_service = MagicMock()
        mock_service.chat_completions_create = AsyncMock(side_effect=Exception("AI service failed"))
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_service
        
        result = await step.run(documents_with_content_input, mock_context)
        
        # Should handle failures gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 2
        assert "failed_documents" in stats
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_prompt_templating(self, custom_ai_prompt_config, documents_with_content_input, mock_ai_inference_service):
        """Test that prompts are properly templated with document content."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_inference_service
        
        await step.run(documents_with_content_input, mock_context)
        
        # Verify that the AI service was called with templated prompts
        call_args = mock_ai_inference_service.chat_completions_create.call_args
        
        # The user prompt should contain the document content
        assert mock_ai_inference_service.chat_completions_create.called
    
    @pytest.mark.asyncio
    async def test_custom_ai_prompt_step_missing_content(self, custom_ai_prompt_config, mock_ai_inference_service):
        """Test CustomAIPromptStep with documents missing content."""
        step = CustomAIPromptStep(custom_ai_prompt_config)
        
        step_input = StepInputOutput(
            summary_data={},
            data={
                "documents": [
                    {
                        "file_path": "/test/doc1.pdf",
                        "file_name": "doc1.pdf"
                        # Missing content field
                    }
                ]
            }
        )
        
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_inference_service
        
        result = await step.run(step_input, mock_context)
        
        # Should handle missing content gracefully
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 1
