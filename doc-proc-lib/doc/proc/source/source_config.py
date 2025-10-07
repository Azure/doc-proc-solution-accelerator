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
    """Represents a data source used in the system."""
    id: str
    name: str
    description: Optional[str] = None
    type: str  # Type of source, e.g., "azure_blob", "azure_files", "sharepoint", etc.
    module_name: str
    module_path: str
    class_name: str
    version: Optional[str] = None
    settings_schema: Optional[SourceConfigSchemaSettings] = None
    ui_metadata: Optional[SourceConfigUIMetadata] = None
    tags: Optional[List[str]] = None

    @classmethod
    def from_yaml_file(cls, file_path: str) -> List["SourceConfig"]:
        """Load source configurations from a YAML file."""
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        
        sources = []
        for source_data in data.get('sources', []):
            sources.append(cls(**source_data))
        
        return sources

    @classmethod
    def from_dict(cls, data: dict) -> "SourceConfig":
        """Create a SourceConfig instance from a dictionary."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert the SourceConfig to a dictionary."""
        return self.dict(exclude_none=True)

    def __str__(self) -> str:
        return f"SourceConfig(id='{self.id}', name='{self.name}', type='{self.type}')"

    def __repr__(self) -> str:
        return f"SourceConfig(id='{self.id}', name='{self.name}', type='{self.type}', module_name='{self.module_name}')"