from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.common import BaseDoc

class ServiceSettingsSchema(BaseModel):
    """Schema definition for individual service setting parameters"""
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    pattern: Optional[str] = None
    env_var: Optional[str] = None
    default: Optional[str | int | float | bool] = None
    minimum: Optional[int | float] = None
    maximum: Optional[int | float] = None
    enum: Optional[List[str]] = None
    sensitive: Optional[bool] = None


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


class ServiceStatus(BaseModel):
    """Service connection status information"""
    status: str = Field(..., description="Status: 'connected', 'error', 'testing', 'unknown'")
    last_tested: Optional[datetime] = None
    error_message: Optional[str] = None
    test_duration_ms: Optional[int] = None


class ServiceCreateRequest(BaseModel):
    """Request to create a new service instance"""
    name: str
    description: Optional[str] = None
    service_catalog_id: str = Field(..., description="ID from service catalog")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Service settings")


class ServiceUpdateRequest(BaseModel):
    """Request to update service settings"""
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ServiceTestConnectionResponse(BaseModel):
    """Response from service connection test"""
    success: bool
    status: str
    message: Optional[str] = None
    duration_ms: Optional[int] = None
    tested_at: datetime


class ServiceInstance(BaseDoc):
    """Service instance based on catalog definition"""
    service_catalog_id: str = Field(..., description="Reference to service catalog ID")
    type: str = Field(..., description="Service type from catalog")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Instance-specific settings")
    catalog_definition: Optional[ServiceCatalogDefinition] = None
    status: str = Field(default="unknown", description="Service instance status")
    connection_status: Optional[ServiceStatus] = None
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None

