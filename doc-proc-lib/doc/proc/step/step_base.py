from __future__ import annotations
from abc import abstractmethod
import pydantic
from typing import List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    # Avoid circular import issues by using string type hints
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext

class StepInstanceConfig(pydantic.BaseModel):
    step_catalog_id: str  # Reference to step id in the step catalog
    name: str  # Instance name in the pipeline
    enabled: bool = True # Whether the step is enabled
    fail_pipeline_on_error: bool = False # Whether to fail the entire pipeline if this step fails
    retry_on_failure: bool = False # Whether to retry the step on failure
    retries: int = 3 # Number of retries for the step in case of failure
    timeout: int = 600 # Timeout for the step in seconds
    fail_step_on_document_error: bool = False  # Whether to fail the step if document processing fails
    debug_mode: bool = False  # Enable debug mode for this step
    condition: Optional[str] = None  # Optional condition to evaluate before running the step
    services: List[str] = []  # References to service instances used by this step
    settings: Optional[dict] = None # Additional settings for the step instance
    

class StepExecutionError(Exception):
    """
    Custom exception for errors during step execution.
    """
    pass

class StepInputOutput(pydantic.BaseModel):
    id: Optional[str] = None
    summary_data: dict = None
    data: dict = None


class StepBase:
    """
    Base class for pipeline steps.

    This class defines the common attributes and methods for all pipeline steps.
    It includes attributes for step configuration, such as name, description,
    enabled status, retry settings, timeout, and more.
    It also defines an abstract method `run` that must be implemented by subclasses 
    to define the step's logic. The `run` method takes a `StepInputOutput` object as 
    input and returns a `StepInputOutput` object as output.
    The `StepInputOutput` class is a Pydantic model that encapsulates the input
    and output data for the step, including an optional ID, summary data, and
    additional data as a dictionary.
    The `StepExecutionError` exception is raised when there is an error during
    step execution, allowing for custom error handling in the pipeline.
    The `StepBase` class is designed to be subclassed, and the `run` method must
    be implemented by subclasses to provide the specific logic for each step in
    the pipeline.
    The `PipelineExecutionContext` type hint is used to provide access to the pipeline
    execution context, allowing steps to interact with the pipeline's execution details
    and services. The `run` method is expected to be asynchronous, allowing for
    non-blocking execution of steps in the pipeline.
    """

    def __init__(self, 
                 instance_config: StepInstanceConfig,
                 **kwargs):

        self.instance_config = instance_config
        self.step_catalog_id = instance_config.step_catalog_id
        self.name = instance_config.name
        self.enabled = instance_config.enabled
        self.fail_pipeline_on_error = instance_config.fail_pipeline_on_error
        self.retry_on_failure = instance_config.retry_on_failure
        self.retries = instance_config.retries
        self.timeout = instance_config.timeout
        # self.description = instance_config.description
        # self.tags = instance_config.tags or []
        self.fail_step_on_document_error = instance_config.fail_step_on_document_error
        self.debug_mode = instance_config.debug_mode
        self.services = instance_config.services or []
        self.settings = instance_config.settings or {}
        self.condition = instance_config.condition  # Condition string to evaluate before running the step
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
        return f"StepBase(step_catalog_id={self.step_catalog_id}, name={self.name}, description={self.description}, tags={self.tags}, params={self.params})"