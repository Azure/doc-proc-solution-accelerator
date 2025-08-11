from pydantic import BaseModel, RootModel
from typing import List, Optional
import yaml

class SourceConfigUIMetadata(BaseModel):
    """UI metadata for source configuration."""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None

class SourceConfigSchemaParameter(BaseModel):
    """Generic parameter for source configuration."""
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

class SourceConfigSchemaSettings(RootModel[dict[str, "SourceConfigSchemaParameter"]]):
    """Generic settings for source configuration."""

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def dict(self, **kwargs):
        return self.root


class SourceConfig(BaseModel):
    """Represents a source used in the system."""
    id: str
    name: str
    description: Optional[str] = None
    type: str  # Type of source, e.g., "azure_blob", "azure_search", etc.
    module_name: str
    module_path: str
    class_name: str
    test_connection: bool = True
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    settings_schema: Optional[SourceConfigSchemaSettings] = None
    ui_metadata: Optional[SourceConfigUIMetadata] = SourceConfigUIMetadata()

    @staticmethod
    def from_dict(config: dict) -> "SourceConfig":
        return SourceConfig(**config)

    @staticmethod
    def from_file(file_path: str) -> List["SourceConfig"]:
        """Load services configuration from a YAML file."""
        if not file_path:
            raise ValueError("File path cannot be empty")
        try:
            with open(file_path, 'r') as file:
                yaml_str = file.read()
                return SourceConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the source configuration: {str(e)}")
        
    @staticmethod
    def from_yaml(yaml_str: str) -> List["SourceConfig"]:
        """Load services configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)
            sources = config.get("sources_catalog", [])
            return [SourceConfig.from_dict(s) for s in sources]
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the source configuration: {str(e)}")


    
