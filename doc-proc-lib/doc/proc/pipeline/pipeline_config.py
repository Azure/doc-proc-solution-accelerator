from pydantic import BaseModel, ValidationError
from typing import List, Optional, Tuple
import yaml

from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig


class PipelineSettingsConfig(BaseModel):
    """Settings for the pipeline execution."""
    enabled: Optional[bool] = True # Whether the pipeline is enabled
    retry_delay: Optional[int] = 5  # Delay in seconds between retries
    timeout: Optional[int] = 300  # Timeout for the entire pipeline execution in seconds
    max_concurrent_runs: Optional[int] = 5  # Maximum number of concurrent runs for the pipeline


class StepInstanceConfig(BaseModel):
    name: str  # Instance name in the pipeline
    step_catalog_id: str  # Reference to step id in the step catalog
    enabled: bool = True # Whether the step is enabled
    fail_step_on_document_error: bool = False  # Whether to fail the step if document processing fails
    debug_mode: bool = False  # Enable debug mode for this step
    services: List[str] = []  # References to service instances used by this step
    settings: Optional[dict] = None


class ServiceInstanceConfig(BaseModel):
    name: str  # Instance name in the pipeline
    service_catalog_id: str  # Reference to service id in the service catalog
    settings: Optional[dict] = None  # Additional settings for the service instance


class PipelineConfig(BaseModel):
    """Configuration for a single pipeline."""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    steps: List[StepInstanceConfig] = []
    execution_sequence: List[str] = None  # Order of step instance names
    settings: PipelineSettingsConfig = PipelineSettingsConfig()
    service_instances: List[ServiceInstanceConfig] = []  # List of service instances used in the pipeline

    @staticmethod
    def from_dict(config: dict) -> "PipelineConfig":
        return PipelineConfig(**config)

    @staticmethod
    def from_file(file_path: str) -> List["PipelineConfig"]:
        """Load steps and pipelines configuration from a YAML file."""
        if not file_path:
            raise ValueError("File path cannot be empty")
        try:
            with open(file_path, 'r') as file:
                yaml_str = file.read()
            return PipelineConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise ValueError(f"Configuration file '{file_path}' not found.")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the pipeline configuration from file: {str(e)}")

    @staticmethod
    def from_yaml(yaml_str: str, step_catalog_config: List[StepConfig] = None, service_catalog_config: List[ServiceConfig] = None) -> List["PipelineConfig"]:
        """Load steps and pipelines configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)

            # Load and validate service instances
            service_instances: List[ServiceInstanceConfig] = []
            if config.get("service_instances"):
                service_instances = [ServiceInstanceConfig(**s) for s in config.get("service_instances", [])]
                for service in service_instances:
                    if not service.name or not service.service_catalog_id:
                        raise ValueError(f"Service instance '{service.name}' is missing required fields: name or service_catalog_id.")

                # Validate service instances against the service catalog
                if service_catalog_config:
                    for service in service_instances:
                        s_found = next((s for s in service_catalog_config if s.id == service.service_catalog_id), None)
                        if not s_found:
                            raise ValueError(f"Service instance '{service.name}' references unknown service catalog id '{service.service_catalog_id}' that could not be found in service catalog configuration. Available services: {[s.id for s in service_catalog_config]}")

            
            # Load and validate pipelines
            if not config.get("pipelines"):
                raise ValueError("No pipelines found in the configuration.")
            
            pipelines = [PipelineConfig.from_dict(p) for p in config.get("pipelines", [])]
            
            for pipeline in pipelines:
                if not pipeline.name or not pipeline.execution_sequence:
                    raise ValueError(f"Pipeline '{pipeline.name}' is missing required fields.")
                
                if not pipeline.steps:
                    raise ValueError(f"Pipeline '{pipeline.name}' has no steps defined.")

                # Validate execution sequence
                if not all(step in [s.name for s in pipeline.steps] for step in pipeline.execution_sequence):
                    raise ValueError(f"Pipeline '{pipeline.name}' has an invalid execution sequence. Some steps in the sequence do not match defined step names.")

                pipeline.service_instances = service_instances  # Assign service instances to the pipeline

                # Validate step instances
                for step in pipeline.steps:
                    # Validate service references
                    for service_name in step.services:
                        if not any(service.name == service_name for service in service_instances):
                            raise ValueError(f"Service '{service_name}' referenced in step '{step.name}' does not exist in the service instances.")
                    
                    # Validate step catalog reference
                    if step_catalog_config:
                        if not any(s.id == step.step_catalog_id for s in step_catalog_config):
                            raise ValueError(f"Step '{step.name}' references unknown step catalog id '{step.step_catalog_id}' that could not be found in the step catalog configuration.")

            return pipelines
        
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except ValidationError as ve:
            raise ValueError(f"Validation error in pipeline configuration: {ve}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the pipeline configuration: {str(e)}")