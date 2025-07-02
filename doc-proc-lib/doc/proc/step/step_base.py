from __future__ import annotations
from abc import abstractmethod
import pydantic
from typing import List, Literal, Optional, Any, TYPE_CHECKING


if TYPE_CHECKING:
    # Avoid circular import issues by using string type hints
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext


class StepExecutionError(Exception):
    """
    Custom exception for errors during step execution.
    """
    pass

class StepInputOutput(pydantic.BaseModel):
    id: Optional[str] = None
    summary_data: Optional[dict] = None
    data: Optional[dict] = None


class StepBase:
    """
    Base class for pipeline steps.
    """

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, debug_mode: bool = False, services: List[str] = None, settings: dict = None, **kwargs):
        self.id = id
        self.name = name
        self.enabled = enabled
        self.description = description
        self.tags = tags or []
        self.debug_mode = debug_mode
        self.services = services or []
        self.settings = settings or {}
        self.params = kwargs


    @abstractmethod
    async def run(self, step_input: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        """
        Run the step with the given input.
        Type hint for context is a string to avoid circular import.
        Import PipelineExecutionContext inside the method if runtime access is needed.
        Use this method to implement the step's logic.
        Use the context to access pipeline execution details and get services if needed.
        """
        # from pipeline.pipeline_base import PipelineExecutionContext  # Uncomment if runtime access is needed
        raise NotImplementedError("Subclasses must implement this method.")


    def __str__(self):
        return f"StepBase(name={self.name}, description={self.description}, tags={self.tags}, params={self.params})"