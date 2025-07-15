"""
Unit tests for pipeline base classes and related components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from doc.proc.pipeline.pipeline_base import (
    PipelineExecutionContext,
    StepExecutionResult,
    PipelineExecutionResult
)
from doc.proc.step.step_base import StepBase, StepInputOutput, StepInstanceConfig
from doc.proc.service.service_base import ServiceBase


class MockStep(StepBase):
    """Mock step for testing."""
    
    async def run(self, step_input: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        return StepInputOutput(
            id=step_input.id,
            summary_data={**step_input.summary_data, "mock_step_executed": True},
            data=step_input.data
        )


class MockService(ServiceBase):
    """Mock service for testing."""
    
    async def test_connection(self) -> bool:
        return True


class TestPipelineExecutionContext:
    """Test cases for PipelineExecutionContext."""
    
    def test_pipeline_execution_context_creation(self):
        """Test creating a PipelineExecutionContext."""
        context = PipelineExecutionContext(
            pipeline_name="test_pipeline",
            execution_id="test_123"
        )
        
        assert context.pipeline_name == "test_pipeline"
        assert context.execution_id == "test_123"
    
    def test_pipeline_execution_context_get_service(self, mock_service):
        """Test getting a service from the execution context."""
        context = PipelineExecutionContext(
            services=[{"name": "test_service", "instance": mock_service}]
        )
        
        retrieved_service = context.get_service("test_service")
        assert retrieved_service == mock_service
    
    def test_pipeline_execution_context_get_service_not_found(self):
        """Test getting a non-existent service returns None."""
        context = PipelineExecutionContext(services=[])
        
        retrieved_service = context.get_service("nonexistent_service")
        assert retrieved_service is None
    
    def test_pipeline_execution_context_dynamic_attributes(self):
        """Test that PipelineExecutionContext accepts dynamic attributes."""
        context = PipelineExecutionContext(
            custom_attribute="custom_value",
            another_attribute=123
        )
        
        assert context.custom_attribute == "custom_value"
        assert context.another_attribute == 123


class TestStepExecutionResult:
    """Test cases for StepExecutionResult."""
    
    def test_step_execution_result_creation(self):
        """Test creating a StepExecutionResult."""
        result = StepExecutionResult(
            step_name="test_step",
            result="Succeeded",
            elapsed_time_secs=1.5
        )
        
        assert result.step_name == "test_step"
        assert result.result == "Succeeded"
        assert result.elapsed_time_secs == 1.5
        assert result.reason is None
        assert result.error is None
        assert result.error_message is None
        assert result.error_traceback is None
    
    def test_step_execution_result_with_error(self):
        """Test creating a StepExecutionResult with error information."""
        result = StepExecutionResult(
            step_name="failing_step",
            result="Failed",
            elapsed_time_secs=0.5,
            reason="Step execution failed",
            error="ValueError: Invalid input",
            error_message="Detailed error message",
            error_traceback="Traceback (most recent call last)..."
        )
        
        assert result.step_name == "failing_step"
        assert result.result == "Failed"
        assert result.reason == "Step execution failed"
        assert result.error == "ValueError: Invalid input"
        assert result.error_message == "Detailed error message"
        assert result.error_traceback == "Traceback (most recent call last)..."
    
    def test_step_execution_result_skipped(self):
        """Test creating a StepExecutionResult for a skipped step."""
        result = StepExecutionResult(
            step_name="skipped_step",
            result="Skipped",
            elapsed_time_secs=0.0,
            reason="Condition not met"
        )
        
        assert result.step_name == "skipped_step"
        assert result.result == "Skipped"
        assert result.reason == "Condition not met"
        assert result.elapsed_time_secs == 0.0


class TestPipelineExecutionResult:
    """Test cases for PipelineExecutionResult."""
    
    def test_pipeline_execution_result_creation(self):
        """Test creating a PipelineExecutionResult."""
        step_results = [
            StepExecutionResult(
                step_name="step1",
                result="Succeeded",
                elapsed_time_secs=1.0
            ),
            StepExecutionResult(
                step_name="step2",
                result="Succeeded",
                elapsed_time_secs=2.0
            )
        ]
        
        result = PipelineExecutionResult(
            pipeline_name="test_pipeline",
            result="Succeeded",
            elapsed_time_secs=3.5,
            step_execution_results=step_results,
            summary_data={"total_steps": 2},
            data={"output": "processed"}
        )
        
        assert result.pipeline_name == "test_pipeline"
        assert result.result == "Succeeded"
        assert result.elapsed_time_secs == 3.5
        assert len(result.step_execution_results) == 2
        assert result.summary_data == {"total_steps": 2}
        assert result.data == {"output": "processed"}
    
    def test_pipeline_execution_result_defaults(self):
        """Test PipelineExecutionResult with default values."""
        result = PipelineExecutionResult(
            pipeline_name="test_pipeline",
            elapsed_time_secs=1.0
        )
        
        assert result.pipeline_name == "test_pipeline"
        assert result.result == "NotStarted"  # Default value
        assert result.reason is None
        assert result.step_execution_results == []  # Default empty list
        assert result.summary_data == {}  # Default empty dict
        assert result.data == {}  # Default empty dict
    
    def test_pipeline_execution_result_failed(self):
        """Test creating a PipelineExecutionResult for a failed pipeline."""
        step_results = [
            StepExecutionResult(
                step_name="step1",
                result="Succeeded",
                elapsed_time_secs=1.0
            ),
            StepExecutionResult(
                step_name="step2",
                result="Failed",
                elapsed_time_secs=0.5,
                error="Step failed"
            )
        ]
        
        result = PipelineExecutionResult(
            pipeline_name="failing_pipeline",
            result="Failed",
            elapsed_time_secs=1.5,
            reason="Step2 failed",
            step_execution_results=step_results
        )
        
        assert result.pipeline_name == "failing_pipeline"
        assert result.result == "Failed"
        assert result.reason == "Step2 failed"
        assert len(result.step_execution_results) == 2
        
        # Check that the failed step is properly recorded
        failed_step = result.step_execution_results[1]
        assert failed_step.result == "Failed"
        assert failed_step.error == "Step failed"
    
    def test_pipeline_execution_result_partial_success(self):
        """Test creating a PipelineExecutionResult for partially successful pipeline."""
        step_results = [
            StepExecutionResult(
                step_name="step1",
                result="Succeeded",
                elapsed_time_secs=1.0
            ),
            StepExecutionResult(
                step_name="step2",
                result="Failed",
                elapsed_time_secs=0.5,
                error="Non-critical error"
            ),
            StepExecutionResult(
                step_name="step3",
                result="Succeeded",
                elapsed_time_secs=1.5
            )
        ]
        
        result = PipelineExecutionResult(
            pipeline_name="partial_pipeline",
            result="PartialSucceeded",
            elapsed_time_secs=3.0,
            reason="Some steps failed but pipeline continued",
            step_execution_results=step_results
        )
        
        assert result.pipeline_name == "partial_pipeline"
        assert result.result == "PartialSucceeded"
        assert result.reason == "Some steps failed but pipeline continued"
        assert len(result.step_execution_results) == 3
