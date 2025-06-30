from typing import Optional, List
import pydantic
import yaml

class StepConfigUIMetadata(pydantic.BaseModel):
    """UI metadata for step configuration."""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class StepConfigSchemaParameter(pydantic.BaseModel):
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


class StepConfigSchemaSettings(pydantic.RootModel[dict[str, "StepConfigSchemaParameter"]]):
    """Generic settings for step configuration."""

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def dict(self, **kwargs):
        return self.root


class StepConfig(pydantic.BaseModel):
    """Config class for global pipeline step definitions."""
    
    id: str
    name: str
    description: Optional[str] = None
    type: str
    module_name: str  # Name of the module containing the step implementation
    module_path: str  # Path to the module file
    class_name: str  # Name of the class implementing the step
    tags: Optional[List[str]] = None  # Tags for categorization or filtering
    category: Optional[str] = None  # Category for grouping steps
    version: Optional[str] = None  # Version of the step
    fail_pipeline_on_error: bool = True  # Whether to fail the pipeline if this step fails
    retry_on_failure: bool = True  # Whether to retry the step on failure
    retries: int = 3  # Number of retries if the step fails
    timeout: int = 600  # Timeout for the step in seconds
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
        except pydantic.ValidationError as ve:
            raise ValueError(f"Validation error in pipeline configuration: {ve}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the pipeline configuration: {str(e)}")
        

