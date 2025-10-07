from pydantic import BaseModel, RootModel
from typing import List, Optional
import yaml


class ServiceConfigUIMetadata(BaseModel):
    """UI metadata for service configuration."""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class ServiceConfigSchemaParameter(BaseModel):
    """Generic parameter for service configuration."""
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    pattern: Optional[str] = None
    env_var: Optional[str] = None
    default: Optional[str | int | float] = None
    min: Optional[int | float] = None
    max: Optional[int | float] = None
    enum: Optional[List[str]] = None
    sensitive: Optional[bool] = None


class ServiceConfigSchemaSettings(RootModel[dict[str, "ServiceConfigSchemaParameter"]]):
    """Generic settings for service configuration."""

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def dict(self, **kwargs):
        return self.root


class ServiceConfig(BaseModel):
    """Represents a service used in the system."""
    id: str
    name: str
    description: Optional[str] = None
    type: str  # Type of service, e.g., "azure_blob", "azure_search", etc.
    module_name: str
    module_path: str
    class_name: str
    test_connection: bool = True
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    settings_schema: Optional[ServiceConfigSchemaSettings] = None
    ui_metadata: Optional[ServiceConfigUIMetadata] = ServiceConfigUIMetadata()

    @staticmethod
    def from_dict(config: dict) -> "ServiceConfig":
        return ServiceConfig(**config)

    @staticmethod
    def from_file(file_path: str) -> List["ServiceConfig"]:
        """Load services configuration from a YAML file."""
        if not file_path:
            raise ValueError("File path cannot be empty")
        try:
            with open(file_path, 'r') as file:
                yaml_str = file.read()
                return ServiceConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the service configuration: {str(e)}")
        
    @staticmethod
    def from_yaml(yaml_str: str) -> List["ServiceConfig"]:
        """Load services configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)
            services = config.get("services_catalog", [])
            return [ServiceConfig.from_dict(s) for s in services]
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the service configuration: {str(e)}")


class ServiceInstanceConfig(BaseModel):
    id: Optional[str] = None  # Unique identifier for the service instance
    name: str  # Instance name in the pipeline
    service_catalog_id: str  # Reference to service id in the service catalog
    settings: Optional[dict] = None  # Additional settings for the service instance
