from typing import Optional, List
import pydantic
import yaml


class StepConfig(pydantic.BaseModel):
    """Config class for global pipeline step definitions."""
    
    id: str
    description: Optional[str] = None
    type: str
    module_name: str  # Name of the module containing the step implementation
    module_path: str  # Path to the module file
    class_name: str  # Name of the class implementing the step
    tags: Optional[List[str]] = None  # Tags for categorization or filtering

    @staticmethod
    def from_dict(config: dict) -> "StepConfig":
        return StepConfig(**config)

    @staticmethod
    def from_yaml(yaml_str: str) -> List["StepConfig"]:
        """Load steps and pipelines configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)
            steps = [StepConfig(**s) for s in config.get("steps", [])]
            return steps
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except pydantic.ValidationError as ve:
            raise ValueError(f"Validation error in pipeline configuration: {ve}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the pipeline configuration: {str(e)}")