"""
Unit tests for the StepBase class and related components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from doc.proc.step.step_base import (
    StepBase, 
    StepInstanceConfig, 
    StepInputOutput, 
    StepExecutionError
)
from doc.proc.pipeline.pipeline_base import PipelineExecutionContext


class ConcreteStep(StepBase):
    """Concrete implementation of StepBase for testing."""
    
    async def run(self, step_input: StepInputOutput, context: PipelineExecutionContext, **kwargs) -> StepInputOutput:
        # Simple implementation that adds a processed flag to each document
        documents = step_input.data.get("documents", [])
        for doc in documents:
            doc["processed_by_concrete_step"] = True
        
        return StepInputOutput(
            id=step_input.id,
            summary_data={
                **step_input.summary_data,
                "concrete_step_processed": len(documents)
            },
            data=step_input.data
        )


class FailingStep(StepBase):
    """Step implementation that always fails for testing error handling."""
    
    async def run(self, step_input: StepInputOutput, context: PipelineExecutionContext, **kwargs) -> StepInputOutput:
        raise StepExecutionError("This step always fails")


class TestStepInstanceConfig:
    """Test cases for StepInstanceConfig."""
    
    def test_step_instance_config_creation(self):
        """Test creating a StepInstanceConfig with required fields."""
        config = StepInstanceConfig(
            step_catalog_id="test_step",
            name="test_instance"
        )
        
        assert config.step_catalog_id == "test_step"
        assert config.name == "test_instance"
        assert config.enabled is True  # Default value
        assert config.fail_pipeline_on_error is False  # Default value
        assert config.retry_on_failure is False  # Default value
        assert config.retries == 3  # Default value
        assert config.timeout == 600  # Default value
        assert config.fail_step_on_document_error is False  # Default value
        assert config.debug_mode is False  # Default value
        assert config.condition is None  # Default value
        assert config.services == []  # Default value
        assert config.settings is None  # Default value
    
    def test_step_instance_config_with_all_fields(self):
        """Test creating a StepInstanceConfig with all fields specified."""
        config = StepInstanceConfig(
            step_catalog_id="test_step",
            name="test_instance",
            enabled=False,
            fail_pipeline_on_error=True,
            retry_on_failure=True,
            retries=5,
            timeout=1200,
            fail_step_on_document_error=True,
            debug_mode=True,
            condition="document_type.primary_type == 'pdf'",
            services=["service1", "service2"],
            settings={"key": "value"}
        )
        
        assert config.step_catalog_id == "test_step"
        assert config.name == "test_instance"
        assert config.enabled is False
        assert config.fail_pipeline_on_error is True
        assert config.retry_on_failure is True
        assert config.retries == 5
        assert config.timeout == 1200
        assert config.fail_step_on_document_error is True
        assert config.debug_mode is True
        assert config.condition == "document_type.primary_type == 'pdf'"
        assert config.services == ["service1", "service2"]
        assert config.settings == {"key": "value"}


class TestStepInputOutput:
    """Test cases for StepInputOutput."""
    
    def test_step_input_output_creation(self):
        """Test creating a StepInputOutput with default values."""
        step_io = StepInputOutput()
        
        assert step_io.id is None
        assert step_io.summary_data is None
        assert step_io.data is None
    
    def test_step_input_output_with_data(self):
        """Test creating a StepInputOutput with data."""
        step_io = StepInputOutput(
            id="test_id",
            summary_data={"total": 5},
            data={"documents": ["doc1", "doc2"]}
        )
        
        assert step_io.id == "test_id"
        assert step_io.summary_data == {"total": 5}
        assert step_io.data == {"documents": ["doc1", "doc2"]}


class TestStepBase:
    """Test cases for StepBase."""
    
    def test_step_base_initialization(self, sample_step_config):
        """Test StepBase initialization with config."""
        step = ConcreteStep(sample_step_config)
        
        assert step.instance_config == sample_step_config
        assert step.step_catalog_id == sample_step_config.step_catalog_id
        assert step.name == sample_step_config.name
        assert step.enabled == sample_step_config.enabled
        assert step.fail_pipeline_on_error == sample_step_config.fail_pipeline_on_error
        assert step.retry_on_failure == sample_step_config.retry_on_failure
        assert step.retries == sample_step_config.retries
        assert step.timeout == sample_step_config.timeout
        assert step.fail_step_on_document_error == sample_step_config.fail_step_on_document_error
        assert step.debug_mode == sample_step_config.debug_mode
        assert step.services == sample_step_config.services
        assert step.settings == sample_step_config.settings
        assert step.condition == sample_step_config.condition
    
    def test_step_base_with_additional_params(self, sample_step_config):
        """Test StepBase initialization with additional parameters."""
        step = ConcreteStep(sample_step_config, extra_param="extra_value")
        
        assert step.params == {"extra_param": "extra_value"}
    
    @pytest.mark.asyncio
    async def test_concrete_step_run(self, sample_step_config, sample_step_input, mock_pipeline_context):
        """Test running a concrete step implementation."""
        step = ConcreteStep(sample_step_config)
        
        result = await step.run(sample_step_input, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        assert result.id == sample_step_input.id
        assert "concrete_step_processed" in result.summary_data
        assert result.summary_data["concrete_step_processed"] == 1
        
        # Check that documents were processed
        documents = result.data["documents"]
        assert len(documents) == 1
        assert documents[0]["processed_by_concrete_step"] is True
    
    @pytest.mark.asyncio
    async def test_abstract_step_run_not_implemented(self, sample_step_config, sample_step_input, mock_pipeline_context):
        """Test that StepBase.run raises NotImplementedError."""
        step = StepBase(sample_step_config)
        
        with pytest.raises(NotImplementedError):
            await step.run(sample_step_input, mock_pipeline_context)
    
    @pytest.mark.asyncio
    async def test_failing_step_execution_error(self, sample_step_config, sample_step_input, mock_pipeline_context):
        """Test that StepExecutionError is properly raised."""
        step = FailingStep(sample_step_config)
        
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(sample_step_input, mock_pipeline_context)
        
        assert str(exc_info.value) == "This step always fails"
    
    @pytest.mark.asyncio
    async def test_step_with_empty_documents(self, sample_step_config, sample_empty_step_input, mock_pipeline_context):
        """Test step execution with empty documents list."""
        step = ConcreteStep(sample_step_config)
        
        result = await step.run(sample_empty_step_input, mock_pipeline_context)
        
        assert isinstance(result, StepInputOutput)
        assert result.summary_data["concrete_step_processed"] == 0
        assert result.data["documents"] == []
    
    @pytest.mark.asyncio
    async def test_step_with_multiple_documents(self, sample_step_config, mock_pipeline_context, multiple_documents_data):
        """Test step execution with multiple documents."""
        step_input = StepInputOutput(
            summary_data={"total_documents": len(multiple_documents_data)},
            data={"documents": multiple_documents_data}
        )
        
        step = ConcreteStep(sample_step_config)
        result = await step.run(step_input, mock_pipeline_context)
        
        assert result.summary_data["concrete_step_processed"] == 3
        
        # Check that all documents were processed
        for doc in result.data["documents"]:
            assert doc["processed_by_concrete_step"] is True


class TestStepExecutionError:
    """Test cases for StepExecutionError."""
    
    def test_step_execution_error_creation(self):
        """Test creating a StepExecutionError."""
        error = StepExecutionError("Test error message")
        assert str(error) == "Test error message"
    
    def test_step_execution_error_inheritance(self):
        """Test that StepExecutionError inherits from Exception."""
        error = StepExecutionError("Test error")
        assert isinstance(error, Exception)
