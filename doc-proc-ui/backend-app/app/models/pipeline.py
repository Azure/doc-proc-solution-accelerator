from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field

from .common import BaseDoc


class PipelineStepDefinition(BaseModel):
    """Pipeline step definition from configuration"""
    name: str
    step_catalog_id: str
    enabled: bool = True
    fail_pipeline_on_error: bool = False
    retry_on_failure: bool = False
    retries: int = 3
    timeout: int = 600
    services: List[str] = Field(default_factory=list)
    condition: Optional[str] = None
    fail_step_on_document_error: bool = False
    debug_mode: bool = False
    settings: Dict[str, Any] = Field(default_factory=dict)


class PipelineSettings(BaseModel):
    """Pipeline execution settings"""
    enabled: bool = True
    retry_delay: int = 5
    timeout: int = 300
    max_concurrent_runs: int = 5


class PipelineConfig(BaseModel):
    """Pipeline configuration model"""
    name: str
    description: Optional[str] = None
    version: str = Field(default="1.0")
    steps: List[PipelineStepDefinition] = Field(default_factory=list)
    execution_sequence: List[str] = Field(default_factory=list)
    settings: PipelineSettings = Field(default_factory=PipelineSettings)


class PipelineCreateRequest(BaseModel):
    """Request to create a new pipeline"""
    name: str
    description: Optional[str] = None
    config: Optional[PipelineConfig] = None
    steps: List[str] = Field(default_factory=list, description="Ordered list of step ids (legacy)")


class PipelineInstance(BaseDoc):
    """Pipeline instance based on configuration"""
    version: str = Field(default="1.0", description="Pipeline version")
    steps: List[PipelineStepDefinition] = Field(default_factory=list, description="Pipeline steps")
    execution_sequence: List[str] = Field(default_factory=list, description="Step execution order")
    settings: PipelineSettings = Field(default_factory=PipelineSettings, description="Pipeline settings")
    config_name: Optional[str] = Field(None, description="Reference to pipeline configuration")
    status: str = Field(default="active", description="Pipeline status")


# Legacy model for backward compatibility
class Pipeline(BaseDoc):
    kind: str = Field(default="pipeline")
    steps: List[str] = Field(default_factory=list, description="Ordered list of step ids")
    metadata: Dict[str, str] = Field(default_factory=dict)
