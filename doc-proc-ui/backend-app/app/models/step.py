from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from app.models.common import BaseDoc


class StepSettingsSchema(BaseModel):
    """Schema definition for step settings"""
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    default: Optional[str | int | float | bool] = None
    ui_component: Optional[str] = None
    service_type: Optional[str] = None
    enum: Optional[List[str]] = None
    min: Optional[int | float] = None
    max: Optional[int | float] = None
    multipleOf: Optional[int | float] = None
    pattern: Optional[str] = None

class StepUIMetadata(BaseModel):
    """UI metadata for step display"""
    icon: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class StepCatalogDefinition(BaseModel):
    """Step catalog definition from YAML"""
    id: str
    name: str
    description: str
    module_name: str
    module_path: str
    class_name: str
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    settings_schema: Optional[Dict[str, StepSettingsSchema]] = None
    ui_metadata: Optional[StepUIMetadata] = None


class StepInstance(BaseDoc):
    """Step instance based on catalog definition"""
    step_catalog_id: str = Field(..., description="Reference to step catalog ID")
    enabled: bool = Field(default=True, description="Whether step is enabled")
    fail_pipeline_on_error: bool = Field(default=False, description="Fail pipeline if step fails")
    timeout: int = Field(default=600, description="Step timeout in seconds")
    services: List[str] = Field(default_factory=list, description="Referenced service instances")
    condition: Optional[str] = Field(None, description="Condition for step execution")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Step-specific settings")
    catalog_definition: Optional[StepCatalogDefinition] = None
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None


class StepInstanceCreateRequest(BaseModel):
    """Request to create a new step instance"""
    name: str
    description: Optional[str] = None
    step_catalog_id: str = Field(..., description="ID from step catalog")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Step settings")
    enabled: bool = Field(default=True, description="Whether step is enabled")
    fail_pipeline_on_error: bool = Field(default=False, description="Fail pipeline if step fails")
    timeout: int = Field(default=30, description="Step timeout in seconds")
    services: List[str] = Field(default_factory=list, description="Referenced service instances")
    condition: Optional[str] = Field(None, description="Condition for step execution")
    debug_mode: bool = Field(default=False, description="Enable debug mode")


class StepInstanceUpdateRequest(BaseModel):
    """Request to update a step instance"""
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict, description="Step settings")
    enabled: bool = Field(default=True, description="Whether step is enabled")

