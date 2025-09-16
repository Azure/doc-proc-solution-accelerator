from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field

from app.models.common import BaseDoc

class PipelineSettings(BaseModel):
    """Pipeline execution settings"""
    enabled: bool = True
    retry_delay: int = 5 # in seconds
    timeout: int = 600  # in seconds
    retries: int = 3
    max_concurrent_runs: int = 5

class CreatePipelineRequest(BaseModel):
    """Request to create a new pipeline"""
    id: Optional[str] = None # Optional, will be auto-generated if not provided
    name: str
    description: Optional[str] = None
    steps: Optional[List[str]] = Field(default_factory=list, description="Pipeline steps, references to step instance names")
    execution_sequence: Optional[List[str]] = Field(default_factory=list, description="Step execution order")
    version: Optional[str] = Field(default="1.0", description="Pipeline version")
    settings: Optional[PipelineSettings] = Field(default_factory=PipelineSettings, description="Pipeline settings")
    
class Pipeline(BaseDoc):
    steps: List[str] = Field(default_factory=list, description="Pipeline steps, references to step instance names")
    execution_sequence: List[str] = Field(default_factory=list, description="Step execution order")
    version: Optional[str] = Field(default="1.0", description="Pipeline version")
    settings: Optional[PipelineSettings] = Field(default_factory=PipelineSettings, description="Pipeline settings")
    