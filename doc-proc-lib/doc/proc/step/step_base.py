from __future__ import annotations
from abc import abstractmethod
import pydantic
import logging
import hashlib
from typing import List, Optional, TYPE_CHECKING
from dependencies import get_config
from connectors import CosmosDBClient
from datetime import datetime, timedelta, timezone

if TYPE_CHECKING:
    # Avoid circular import issues by using string type hints
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext

logger = logging.getLogger("doc.proc.step.step_base")

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
    cancel_request : bool = False
    error_count : int = 0

    def __init__(self, message : str, cancel_request = False, error_count = 0):
        super().__init__(message)

        self.cancel_request = cancel_request
        self.error_count = error_count

class StepInputOutput(pydantic.BaseModel):
    id: Optional[str] = None
    summary_data: dict = None
    data: dict = None
    remove_state : bool = False

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

        self.config = get_config()

        self.cosmos = CosmosDBClient(self.config)

        # Initialize condition evaluator if condition is provided
        if self.condition:
            from doc.proc.utils.secure_condition_evaluator import SecureConditionEvaluator
            self.condition_evaluator = SecureConditionEvaluator()
        else:
            self.condition_evaluator = None


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
    
    async def get_state(self, document):
        document_state = self.cosmos.get_document('doc-proc', document.get("id"))
        if document_state == None:
            document_state = {
                "id": document.get("id"),
                "steps": [],
                "modify_date" : str(datetime.now(timezone.utc)),
                "create_date" : str(datetime.now(timezone.utc)),
                "status" : "new",
                "data": {
                    "source_name": document.get("source_name"),
                    "file_path": document.get("file_path"),
                    "file_type": document.get("file_type"),
                    "modify_date" : str(document.get("modify_date", datetime.now(timezone.utc))),
                    "create_date" : str(document.get("create_date", datetime.now(timezone.utc)))
                }
            }
            await self.save_state(document_state)
        return document_state

    async def save_state(self, document_state):
        document_state['modify_date'] = str(datetime.now(timezone.utc))
        #document_state['status'] = "processing"
        await self.cosmos.upsert_document('doc-proc', document_state)

    async def should_process(self, document_state, document):
        
        #document have been modified
        if document_state['data']['modify_date'] != document.get("modify_date"):
            return False
        
        #we did this step already
        if self.name in document_state['steps']:
            return False

        return True

    def evaluate_document_condition(self, document: dict, step_input: StepInputOutput) -> bool:
        """
        Evaluate a step's condition against a specific document.
        
        Args:
            document: The document to evaluate the condition against
            step_input: The current input data for the step
            
        Returns:
            bool: True if the condition is met or no condition is set, False otherwise
            
        Raises:
            Exception: If condition evaluation fails
        """
        if not self.condition or not self.condition_evaluator:
            return True  # No condition means always process
        
        try:
            logger.debug(f"Evaluating condition for step {self.name} on document: {self.condition}")
            
            # Create evaluation context with document data
            evaluation_data = {}
            
            # Add document data to evaluation context
            if document:
                evaluation_data.update(document)
            
            # Add step input data to evaluation context
            if step_input.data:
                evaluation_data.update(step_input.data)
            
            # Add summary data to evaluation context
            if step_input.summary_data:
                evaluation_data.update(step_input.summary_data)
            
            # Evaluate the condition
            condition_group = self.condition_evaluator.parse_condition_string(self.condition)
            result = self.condition_evaluator.evaluate(condition_group, evaluation_data)
            
            logger.debug(f"Condition evaluation result for step {self.name} on document: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating condition for step {self.name} on document: {e}")
            raise Exception(f"Failed to evaluate condition '{self.condition}': {str(e)}")


    def filter_documents_by_condition(self, documents: List[dict], step_input: StepInputOutput) -> List[dict]:
        """
        Filter documents based on the step's condition.
        
        Args:
            documents: List of documents to filter
            step_input: The current input data for the step
            
        Returns:
            List[dict]: Filtered list of documents that meet the condition
        """
        if not self.condition:
            return documents  # No condition means process all documents
        
        filtered_documents = []
        for document in documents:
            try:
                if self.evaluate_document_condition(document, step_input):
                    filtered_documents.append(document)
                else:
                    logger.debug(f"Document skipped due to condition not met: {self.condition}")
            except Exception as e:
                logger.warning(f"Error evaluating condition for document, skipping: {e}")
                # Continue processing other documents even if one fails condition evaluation
                continue
        
        logger.info(f"Step {self.name}: {len(filtered_documents)} out of {len(documents)} documents meet the condition")
        return filtered_documents

    def get_service(self, context: "PipelineExecutionContext", name: str, type : str = None):
        """
        Get the Service from the context.

        :param context: PipelineExecutionContext instance.
        :return: Service instance.
        """
        if not context or not hasattr(context, 'get_service'):
            logger.error("Invalid context provided. Cannot retrieve Service.")
            return None

        cs = context.get_service(name)
        
        if type != None:
            if cs and cs.type == type:
                return cs

        return cs
    
    def generate_sha1_hash(self, input_string: str) -> str:
        """
        Generates a sha1 hash from a given string.
        """
        # Encode the string to bytes, as hash functions operate on bytes
        encoded_string = input_string.encode('utf-8')
        # Create a SHA1 hash object
        sha1_hash = hashlib.sha1()
        # Update the hash object with the encoded string
        sha1_hash.update(encoded_string)
        # Get the hexadecimal representation of the hash
        return sha1_hash.hexdigest()

    def __str__(self):
        return f"StepBase(step_catalog_id={self.step_catalog_id}, name={self.name}, description={self.description}, tags={self.tags}, params={self.params})"