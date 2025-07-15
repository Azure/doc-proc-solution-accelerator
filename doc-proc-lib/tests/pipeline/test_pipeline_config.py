"""
Unit tests for pipeline configuration classes.
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open
from pydantic import ValidationError

from doc.proc.pipeline.pipeline_config import (
    PipelineSettingsConfig,
    ServiceInstanceConfig,
    PipelineConfig
)
from doc.proc.step.step_base import StepInstanceConfig
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig


class TestPipelineSettingsConfig:
    """Test cases for PipelineSettingsConfig."""
    
    def test_pipeline_settings_config_defaults(self):
        """Test PipelineSettingsConfig with default values."""
        settings = PipelineSettingsConfig()
        
        assert settings.enabled is True
        assert settings.retry_delay == 5
        assert settings.timeout == 300
        assert settings.max_concurrent_runs == 5
    
    def test_pipeline_settings_config_custom_values(self):
        """Test PipelineSettingsConfig with custom values."""
        settings = PipelineSettingsConfig(
            enabled=False,
            retry_delay=10,
            timeout=600,
            max_concurrent_runs=3
        )
        
        assert settings.enabled is False
        assert settings.retry_delay == 10
        assert settings.timeout == 600
        assert settings.max_concurrent_runs == 3
    
    def test_pipeline_settings_config_from_dict(self):
        """Test creating PipelineSettingsConfig from dictionary."""
        config_dict = {
            "enabled": True,
            "retry_delay": 15,
            "timeout": 900,
            "max_concurrent_runs": 2
        }
        
        settings = PipelineSettingsConfig(**config_dict)
        
        assert settings.enabled is True
        assert settings.retry_delay == 15
        assert settings.timeout == 900
        assert settings.max_concurrent_runs == 2


class TestServiceInstanceConfig:
    """Test cases for ServiceInstanceConfig."""
    
    def test_service_instance_config_creation(self):
        """Test creating a ServiceInstanceConfig."""
        service_config = ServiceInstanceConfig(
            name="test_service_instance",
            service_catalog_id="azure_ai_inference",
            settings={"endpoint": "https://test.openai.azure.com/"}
        )
        
        assert service_config.name == "test_service_instance"
        assert service_config.service_catalog_id == "azure_ai_inference"
        assert service_config.settings == {"endpoint": "https://test.openai.azure.com/"}
    
    def test_service_instance_config_without_settings(self):
        """Test ServiceInstanceConfig without optional settings."""
        service_config = ServiceInstanceConfig(
            name="minimal_service",
            service_catalog_id="sample_service"
        )
        
        assert service_config.name == "minimal_service"
        assert service_config.service_catalog_id == "sample_service"
        assert service_config.settings is None
    
    def test_service_instance_config_validation_error(self):
        """Test ServiceInstanceConfig validation with missing required fields."""
        with pytest.raises(ValidationError):
            ServiceInstanceConfig(
                name="test_service"
                # Missing service_catalog_id
            )


class TestPipelineConfig:
    """Test cases for PipelineConfig."""
    
    @pytest.fixture
    def sample_step_configs(self):
        """Fixture for sample step configurations."""
        return [
            StepInstanceConfig(
                step_catalog_id="pdf_text_extractor",
                name="extract_pdf_text",
                services=["ai_inference_service"]
            ),
            StepInstanceConfig(
                step_catalog_id="ai_search_index_writer",
                name="index_documents",
                services=["ai_search_service"]
            )
        ]
    
    @pytest.fixture
    def sample_service_instances(self):
        """Fixture for sample service instances."""
        return [
            ServiceInstanceConfig(
                name="ai_inference_service",
                service_catalog_id="azure_ai_inference",
                settings={"endpoint": "https://test.openai.azure.com/"}
            ),
            ServiceInstanceConfig(
                name="ai_search_service",
                service_catalog_id="azure_ai_search",
                settings={"endpoint": "https://test-search.search.windows.net"}
            )
        ]
    
    @pytest.fixture
    def sample_step_catalog(self):
        """Fixture for sample step catalog."""
        return [
            StepConfig(
                id="pdf_text_extractor",
                name="PDF Text Extractor",
                description="Extracts text from PDF files"
            ),
            StepConfig(
                id="ai_search_index_writer",
                name="AI Search Index Writer",
                description="Writes documents to AI Search index"
            )
        ]
    
    @pytest.fixture
    def sample_service_catalog(self):
        """Fixture for sample service catalog."""
        return [
            ServiceConfig(
                id="azure_ai_inference",
                name="Azure AI Inference Service",
                description="Azure AI inference service"
            ),
            ServiceConfig(
                id="azure_ai_search",
                name="Azure AI Search Service",
                description="Azure AI search service"
            )
        ]
    
    def test_pipeline_config_creation(self, sample_step_configs, sample_service_instances):
        """Test creating a basic PipelineConfig."""
        pipeline = PipelineConfig(
            name="test_pipeline",
            description="A test pipeline",
            version="1.0.0",
            steps=sample_step_configs,
            execution_sequence=["extract_pdf_text", "index_documents"],
            service_instances=sample_service_instances
        )
        
        assert pipeline.name == "test_pipeline"
        assert pipeline.description == "A test pipeline"
        assert pipeline.version == "1.0.0"
        assert len(pipeline.steps) == 2
        assert pipeline.execution_sequence == ["extract_pdf_text", "index_documents"]
        assert len(pipeline.service_instances) == 2
        assert isinstance(pipeline.settings, PipelineSettingsConfig)
    
    def test_pipeline_config_minimal(self):
        """Test creating minimal PipelineConfig with required fields only."""
        pipeline = PipelineConfig(name="minimal_pipeline")
        
        assert pipeline.name == "minimal_pipeline"
        assert pipeline.description is None
        assert pipeline.version is None
        assert pipeline.steps == []
        assert pipeline.execution_sequence is None
        assert isinstance(pipeline.settings, PipelineSettingsConfig)
        assert pipeline.service_instances == []
    
    def test_pipeline_config_from_dict(self, sample_step_configs):
        """Test creating PipelineConfig from dictionary."""
        config_dict = {
            "name": "dict_pipeline",
            "description": "Pipeline from dict",
            "steps": [step.dict() for step in sample_step_configs],
            "execution_sequence": ["extract_pdf_text", "index_documents"]
        }
        
        pipeline = PipelineConfig.from_dict(config_dict)
        
        assert pipeline.name == "dict_pipeline"
        assert pipeline.description == "Pipeline from dict"
        assert len(pipeline.steps) == 2
    
    def test_pipeline_config_validation_error(self):
        """Test PipelineConfig validation with invalid data."""
        with pytest.raises(ValidationError):
            PipelineConfig()  # Missing required name field


class TestPipelineConfigYAMLLoading:
    """Test cases for YAML loading functionality."""
    
    @pytest.fixture
    def valid_yaml_config(self):
        """Fixture for valid YAML configuration."""
        return """
service_instances:
  - name: ai_inference_service
    service_catalog_id: azure_ai_inference
    settings:
      endpoint: https://test.openai.azure.com/
      api_key: test_key
  - name: ai_search_service
    service_catalog_id: azure_ai_search
    settings:
      endpoint: https://test-search.search.windows.net
      api_key: test_search_key

pipelines:
  - name: document_processing_pipeline
    description: Main document processing pipeline
    version: "1.0.0"
    steps:
      - step_catalog_id: pdf_text_extractor
        name: extract_pdf_text
        services: 
          - ai_inference_service
        settings:
          prompts:
            system: Extract text from PDF
            user: Process this document
      - step_catalog_id: ai_search_index_writer
        name: index_documents
        services:
          - ai_search_service
        settings:
          index_name: documents
    execution_sequence:
      - extract_pdf_text
      - index_documents
    settings:
      enabled: true
      timeout: 600
      max_concurrent_runs: 3
"""
    
    @pytest.fixture
    def sample_step_catalog(self):
        """Fixture for step catalog."""
        return [
            StepConfig(id="pdf_text_extractor", name="PDF Extractor", description="Extract PDF text"),
            StepConfig(id="ai_search_index_writer", name="Search Writer", description="Write to search index")
        ]
    
    @pytest.fixture
    def sample_service_catalog(self):
        """Fixture for service catalog."""
        return [
            ServiceConfig(id="azure_ai_inference", name="AI Inference", description="AI service"),
            ServiceConfig(id="azure_ai_search", name="AI Search", description="Search service")
        ]
    
    def test_pipeline_config_from_yaml_success(self, valid_yaml_config, sample_step_catalog, sample_service_catalog):
        """Test successful YAML loading with validation."""
        pipelines = PipelineConfig.from_yaml(
            valid_yaml_config,
            step_catalog_config=sample_step_catalog,
            service_catalog_config=sample_service_catalog
        )
        
        assert len(pipelines) == 1
        pipeline = pipelines[0]
        
        assert pipeline.name == "document_processing_pipeline"
        assert pipeline.description == "Main document processing pipeline"
        assert pipeline.version == "1.0.0"
        assert len(pipeline.steps) == 2
        assert len(pipeline.service_instances) == 2
        assert pipeline.execution_sequence == ["extract_pdf_text", "index_documents"]
        assert pipeline.settings.timeout == 600
        assert pipeline.settings.max_concurrent_runs == 3
    
    def test_pipeline_config_from_yaml_without_catalogs(self, valid_yaml_config):
        """Test YAML loading without catalog validation."""
        pipelines = PipelineConfig.from_yaml(valid_yaml_config)
        
        assert len(pipelines) == 1
        pipeline = pipelines[0]
        assert pipeline.name == "document_processing_pipeline"
    
    def test_pipeline_config_from_yaml_empty_string(self):
        """Test YAML loading with empty string."""
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml("")
        
        assert "YAML string cannot be empty" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_invalid_yaml(self):
        """Test YAML loading with invalid YAML syntax."""
        invalid_yaml = """
        pipelines:
          - name: test
            invalid: [unclosed bracket
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(invalid_yaml)
        
        assert "Invalid YAML format" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_no_pipelines(self):
        """Test YAML loading with no pipelines section."""
        yaml_without_pipelines = """
        service_instances:
          - name: test_service
            service_catalog_id: test_service_type
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(yaml_without_pipelines)
        
        assert "No pipelines found in the configuration" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_missing_pipeline_fields(self):
        """Test YAML loading with missing required pipeline fields."""
        yaml_missing_fields = """
        pipelines:
          - description: Pipeline without name
            steps: []
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(yaml_missing_fields)
        
        assert "missing required fields" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_no_steps(self):
        """Test YAML loading with pipeline that has no steps."""
        yaml_no_steps = """
        pipelines:
          - name: empty_pipeline
            execution_sequence: []
            steps: []
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(yaml_no_steps)
        
        assert "has no steps defined" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_invalid_execution_sequence(self):
        """Test YAML loading with invalid execution sequence."""
        yaml_invalid_sequence = """
        pipelines:
          - name: invalid_sequence_pipeline
            steps:
              - step_catalog_id: test_step
                name: actual_step
            execution_sequence:
              - nonexistent_step
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(yaml_invalid_sequence)
        
        assert "invalid execution sequence" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_invalid_service_reference(self):
        """Test YAML loading with invalid service reference in step."""
        yaml_invalid_service = """
        service_instances:
          - name: existing_service
            service_catalog_id: test_service
        
        pipelines:
          - name: invalid_service_pipeline
            steps:
              - step_catalog_id: test_step
                name: test_step_instance
                services:
                  - nonexistent_service
            execution_sequence:
              - test_step_instance
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(yaml_invalid_service)
        
        assert "does not exist in the service instances" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_unknown_step_catalog_id(self, sample_service_catalog):
        """Test YAML loading with unknown step catalog ID."""
        yaml_unknown_step = """
        service_instances:
          - name: test_service
            service_catalog_id: azure_ai_inference
        
        pipelines:
          - name: unknown_step_pipeline
            steps:
              - step_catalog_id: unknown_step_type
                name: test_step
                services: []
            execution_sequence:
              - test_step
        """
        
        step_catalog = [
            StepConfig(id="known_step", name="Known Step", description="A known step")
        ]
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(
                yaml_unknown_step,
                step_catalog_config=step_catalog,
                service_catalog_config=sample_service_catalog
            )
        
        assert "unknown step catalog id" in str(exc_info.value)
    
    def test_pipeline_config_from_yaml_unknown_service_catalog_id(self, sample_step_catalog):
        """Test YAML loading with unknown service catalog ID."""
        yaml_unknown_service = """
        service_instances:
          - name: test_service
            service_catalog_id: unknown_service_type
        
        pipelines:
          - name: test_pipeline
            steps:
              - step_catalog_id: pdf_text_extractor
                name: test_step
                services: []
            execution_sequence:
              - test_step
        """
        
        service_catalog = [
            ServiceConfig(id="known_service", name="Known Service", description="A known service")
        ]
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(
                yaml_unknown_service,
                step_catalog_config=sample_step_catalog,
                service_catalog_config=service_catalog
            )
        
        assert "unknown service catalog id" in str(exc_info.value)
    
    @patch('doc.proc.utils.secure_condition_evaluator.validate_condition')
    def test_pipeline_config_from_yaml_invalid_condition(self, mock_validate_condition):
        """Test YAML loading with invalid step condition."""
        mock_validate_condition.return_value = ["Invalid syntax in condition"]
        
        yaml_invalid_condition = """
        pipelines:
          - name: invalid_condition_pipeline
            steps:
              - step_catalog_id: test_step
                name: test_step_instance
                condition: "invalid condition syntax"
                services: []
            execution_sequence:
              - test_step_instance
        """
        
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_yaml(yaml_invalid_condition)
        
        assert "Invalid condition in step" in str(exc_info.value)
    
    @patch('doc.proc.utils.secure_condition_evaluator.validate_condition')
    def test_pipeline_config_from_yaml_valid_condition(self, mock_validate_condition):
        """Test YAML loading with valid step condition."""
        mock_validate_condition.return_value = []  # No errors
        
        yaml_valid_condition = """
        pipelines:
          - name: valid_condition_pipeline
            steps:
              - step_catalog_id: test_step
                name: test_step_instance
                condition: "document_type.primary_type == 'pdf'"
                services: []
            execution_sequence:
              - test_step_instance
        """
        
        pipelines = PipelineConfig.from_yaml(yaml_valid_condition)
        
        assert len(pipelines) == 1
        assert pipelines[0].steps[0].condition == "document_type.primary_type == 'pdf'"


class TestPipelineConfigFileLoading:
    """Test cases for file loading functionality."""
    
    def test_pipeline_config_from_file_success(self):
        """Test successful file loading."""
        yaml_content = """
        pipelines:
          - name: file_test_pipeline
            steps:
              - step_catalog_id: test_step
                name: test_step_instance
                services: []
            execution_sequence:
              - test_step_instance
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            pipelines = PipelineConfig.from_file(temp_file)
            
            assert len(pipelines) == 1
            assert pipelines[0].name == "file_test_pipeline"
        
        finally:
            os.unlink(temp_file)
    
    def test_pipeline_config_from_file_empty_path(self):
        """Test file loading with empty file path."""
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_file("")
        
        assert "File path cannot be empty" in str(exc_info.value)
    
    def test_pipeline_config_from_file_not_found(self):
        """Test file loading with non-existent file."""
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_file("/nonexistent/path/config.yaml")
        
        assert "Configuration file '/nonexistent/path/config.yaml' not found" in str(exc_info.value)
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_pipeline_config_from_file_permission_error(self, mock_open):
        """Test file loading with permission error."""
        with pytest.raises(ValueError) as exc_info:
            PipelineConfig.from_file("/restricted/config.yaml")
        
        assert "An error occurred while loading the pipeline configuration from file" in str(exc_info.value)
