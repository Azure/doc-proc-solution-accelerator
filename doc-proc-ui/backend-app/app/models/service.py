from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from .common import BaseDoc


class ServiceSettingsSchema(BaseModel):
    """Schema definition for service settings"""
    type: str
    default: Optional[str] = None
    enum: Optional[List[str]] = None
    maximum: Optional[int] = None
    pattern: Optional[str] = None


class ServiceUIMetadata(BaseModel):
    """UI metadata for service display"""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class ServiceCatalogDefinition(BaseModel):
    """Service catalog definition from YAML"""
    id: str
    name: str
    description: str
    type: str
    module_name: str
    module_path: str
    class_name: str
    test_connection: bool = False
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    settings_schema: Optional[Dict[str, ServiceSettingsSchema]] = None
    ui_metadata: Optional[ServiceUIMetadata] = None


class ServiceInstance(BaseDoc):
    """Service instance based on catalog definition"""
    service_catalog_id: str = Field(..., description="Reference to service catalog ID")
    type: str = Field(..., description="Service type from catalog")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Instance-specific settings")
    catalog_definition: Optional[ServiceCatalogDefinition] = None
    status: str = Field(default="active", description="Service instance status")


# Legacy model for backward compatibility
class ServiceConfig(BaseModel):
    type: str = Field(..., description="Service type, e.g., openai, formrecognizer")
    config: Dict[str, str] = Field(default_factory=dict)


class Service(BaseDoc):
    kind: str = Field(default="service")
    spec: ServiceConfig
