from typing import Optional, List
from pydantic import BaseModel, RootModel, ValidationError
import yaml


class StepConfigUIMetadata(BaseModel):
    """UI metadata for step configuration."""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class StepConfigSchemaParameter(BaseModel):
    """Generic parameter for step configuration."""
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    ui_component: Optional[str] = None  # UI component type for rendering in the UI
    service_type: Optional[str] = None  # Type of service for service selector components
    pattern: Optional[str] = None
    default: Optional[str | int | float] = None
    min: Optional[int | float] = None
    max: Optional[int | float] = None
    multipleOf: Optional[float] = None  # For numeric types, specifies the step size
    enum: Optional[List[str]] = None


class StepConfigSchemaSettings(RootModel[dict[str, "StepConfigSchemaParameter"]]):
    """Generic settings for step configuration."""

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def dict(self, **kwargs):
        return self.root


class StepConfig(BaseModel):
    """Config class for global pipeline step catalog definitions."""
    
    id: str
    name: str
    description: Optional[str] = None
    module_name: str  # Name of the module containing the step implementation
    module_path: str  # Path to the module file
    class_name: str  # Name of the class implementing the step
    tags: Optional[List[str]] = None  # Tags for categorization or filtering
    category: Optional[str] = None  # Category for grouping steps
    version: Optional[str] = None  # Version of the step
    settings_schema: Optional[StepConfigSchemaSettings] = None
    ui_metadata: Optional[StepConfigUIMetadata] = StepConfigUIMetadata()

    @staticmethod
    def from_dict(config: dict) -> "StepConfig":
        return StepConfig(**config)

    @staticmethod
    def from_file(file_path: str) -> List["StepConfig"]:
        """Load steps configuration from a YAML file."""
        if not file_path:
            raise ValueError("File path cannot be empty")
        try:
            with open(file_path, 'r') as file:
                yaml_str = file.read()
                return StepConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the step configuration: {str(e)}")
        
    @staticmethod
    def from_yaml(yaml_str: str) -> List["StepConfig"]:
        """Load steps and pipelines configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)
            steps = [StepConfig(**s) for s in config.get("step_catalog", [])]
            return steps
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except ValidationError as ve:
            raise ValueError(f"Validation error in pipeline configuration: {ve}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the pipeline configuration: {str(e)}")
        

class StepInstanceConfig(BaseModel):
    """Configuration for a step instance in a pipeline."""
    
    id: Optional[str] = None  # Unique identifier for the step instance
    step_catalog_id: str  # Reference to step id in the step catalog
    name: str  # Instance name in the pipeline
    enabled: bool = True # Whether the step is enabled
    fail_pipeline_on_error: bool = False # Whether to fail the entire pipeline if this step fails
    retry_on_failure: bool = False # Whether to retry the step on failure
    retries: int = 3 # Number of retries for the step in case of failure
    timeout: int = 600 # Timeout for the step in seconds
    debug_mode: bool = False  # Enable debug mode for this step
    condition: Optional[str] = None  # Optional condition to evaluate before running the step
    services: List[str] = []  # References to service instances used by this step
    settings: Optional[dict] = None # Additional settings for the step instance