from pydantic import BaseModel, ValidationError
from typing import List, Optional, Tuple
import yaml


class StepInstanceConfig(BaseModel):
    name: str  # Instance name in the pipeline
    step_id: str  # Reference to StepConfig id
    enabled: bool = True
    settings: Optional[dict] = None


class PipelineConfig(BaseModel):
    """Configuration for a single pipeline."""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    updated_at: Optional[str] = None  # ISO 8601 format
    step_instances: List[StepInstanceConfig] = []
    execution_sequence: List[str] = None  # Order of step instance names
    settings: Optional[dict] = None  # Additional settings for the pipeline

    @staticmethod
    def from_dict(config: dict) -> "PipelineConfig":
        return PipelineConfig(**config)

    @staticmethod
    def from_yaml(yaml_str: str) -> List["PipelineConfig"]:
        """Load steps and pipelines configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)
            pipelines = [PipelineConfig.from_dict(p) for p in config.get("pipelines", [])]
            return pipelines
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except ValidationError as ve:
            raise ValueError(f"Validation error in pipeline configuration: {ve}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the pipeline configuration: {str(e)}")