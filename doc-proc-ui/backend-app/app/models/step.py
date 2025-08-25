from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from .common import BaseDoc


class StepSettingsSchema(BaseModel):
    """Schema definition for step settings"""
    type: str
    default: Optional[str] = None
    ui_component: Optional[str] = None
    enum: Optional[List[str]] = None
    maximum: Optional[int] = None


class StepUIMetadata(BaseModel):
    """UI metadata for step display"""
    icon: Optional[str] = None
    color: Optional[str] = None
    description_short: Optional[str] = None
    description_long: Optional[str] = None


class StepCatalogDefinition(BaseModel):
    """Step catalog definition from YAML"""
    id: str
    name: str
    description: str
    type: str
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
    type: str = Field(..., description="Step type from catalog")
    module_name: str = Field(..., description="Python module name")
    module_path: str = Field(..., description="Path to module file")
    class_name: str = Field(..., description="Class name to instantiate")
    enabled: bool = Field(default=True, description="Whether step is enabled")
    fail_pipeline_on_error: bool = Field(default=False, description="Fail pipeline if step fails")
    retry_on_failure: bool = Field(default=False, description="Retry step on failure")
    retries: int = Field(default=3, description="Number of retries")
    timeout: int = Field(default=600, description="Step timeout in seconds")
    services: List[str] = Field(default_factory=list, description="Referenced service instances")
    condition: Optional[str] = Field(None, description="Condition for step execution")
    fail_step_on_document_error: bool = Field(default=False, description="Fail step on document error")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Step-specific settings")
    catalog_definition: Optional[StepCatalogDefinition] = None
    status: str = Field(default="active", description="Step instance status")


# Legacy models for backward compatibility
class StepIO(BaseModel):
    inputs: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)


class Step(BaseDoc):
    kind: str = Field(default="step")
    type: str
    service_id: Optional[str] = None
    params: Dict[str, str] = Field(default_factory=dict)
    io: StepIO = Field(default_factory=StepIO)
