from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SourceInstanceConfig(BaseModel):
    """Configuration for a source instance in a pipeline."""
    
    name: str = Field(..., description="Name of the source instance")
    source_catalog_id: str = Field(..., description="ID of the source in the source catalog")
    description: Optional[str] = Field(None, description="Description of the source instance")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Source-specific settings")
    enabled: bool = Field(True, description="Whether the source instance is enabled")
    test_connection: bool = Field(True, description="Whether to test connection on initialization")
