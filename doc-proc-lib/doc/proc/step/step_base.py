from __future__ import annotations
from abc import abstractmethod
import pydantic
import logging
import json
import base64
import hashlib

from typing import List, Optional, TYPE_CHECKING, Dict
from datetime import datetime, timedelta, timezone

from doc.proc.models.content_identifier import ContentIdentifier

if TYPE_CHECKING:
    # Avoid circular import issues by using string type hints
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext

logger = logging.getLogger("doc.proc.step.step_base")

class StepInstanceConfig(pydantic.BaseModel):
    id : str
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
    id: ContentIdentifier = None
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

        from dependencies import get_config
        self.config = get_config()

        from connectors import CosmosDBClient
        self.cosmos = CosmosDBClient(self.config)

        # Initialize condition evaluator if condition is provided
        if self.condition:
            from doc.proc.utils.secure_condition_evaluator import SecureConditionEvaluator
            self.condition_evaluator = SecureConditionEvaluator()
        else:
            self.condition_evaluator = None

    def _get_model(self, model_name: str = 'CHAT_DEPLOYMENT_NAME') -> Dict:
        model_deployments = self.config.get("MODEL_DEPLOYMENTS", default='[]').replace("'", "\"")

        try:
            print(f"Model deployments: {model_deployments}")
            logging.info(f"Model deployments: {model_deployments}")

            json_model_deployments = json.loads(model_deployments)

            #get the canonical_name of 'CHAT_DEPLOYMENT_NAME'
            for deployment in json_model_deployments:
                if deployment.get("canonical_name") == model_name:
                    return deployment
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON for model deployments: {e}")
            raise ValueError(f"Invalid model deployments configuration: {model_deployments}")
            
        return None
    
    async def _get_source_isntance  (self, document: dict, context) -> object:
        source = document.get("source_name")

        if not source:
            logger.error(f"No source found in document: {document}.")
            raise StepExecutionError(f"No source found in document: {document}.")

        # Find the source by name by iterating
        source_instance = None
        for src in context.sources:
            if src["instance"].name == source:
                source_instance = src["instance"]
                break

        if not source_instance:
            logger.error(f"No source instance found for: {document['source_name']}.")
            raise StepExecutionError(f"No source instance found for: {document['source_name']}.")

        return source_instance
    
    async def _get_source_content(self, document: dict, context) -> str:
        
        source_instance = self._get_source_isntance(document, context)

        content = await source_instance.get_content(document["content_uri"])

        if not content:
            logger.error(f"No content found for: {document['content_uri']}.")
            raise StepExecutionError(f"No content found for: {document['content_uri']}.")
        
        return content
    
    async def _get_content_metadata(self, document: dict, context) -> dict:
        source_instance = self._get_source_isntance(document, context)

        content_metadata = await source_instance.get_content_metadata(document["content_uri"])

        if not content_metadata:
            logger.error(f"No content metadata found for: {document['content_uri']}.")

        return content_metadata
    
    async def _get_content_security(self, document: dict, context) -> dict:
        source_instance = self._get_source_isntance(document, context)

        content_metadata_security = await source_instance.get_content_security(document["content_uri"])

        if not content_metadata_security:
            logger.error(f"No content metadata security found for: {document['content_uri']}.")

        return content_metadata_security

    def _get_content(self, document: dict) -> str:
        content = ""
        chunks = document.get("chunks", [])
        if len(chunks) > 0:
            for chunk in chunks:
                content += chunk.get("raw_text", "")
        else:
            encoding = document.get("encoding", "base64")
            temp = document.get("content", "")

            if type(temp) == bytes:
                if encoding == "base64":
                    content = temp.decode('utf-8')
                else:
                    content = temp.decode(encoding)
            elif type(temp) == str:
                content = temp

        return content
    
    def _parse_settings(self, settings: Dict) -> Dict:
        """Parse environment variables in the given settings dictionary."""
        parsed_settings = {}
        for key, value in settings.items():
            parsed_settings[key] = self._parse_env(value)
        return parsed_settings
     
    def _parse_env(self, value: str) -> str:
        """Parse environment variables in the given value."""
        if not value:
            return value
        
        if isinstance(value, str) and value.startswith("$"):
            env_var = value[1:].replace("{", "").replace("}", "")
            value = self.config.get(env_var, value)
        
            if not value:
                raise ValueError(f"Environment variable '{env_var}' is not set or empty. Ensure it is defined in your environment or .env file.")

        return value

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
    
    
    def convert_png_to_base64(self, png_path: str) -> str:
        """
        Convert a PNG file to a base64 encoded string.
        
        :param png_path: Path to the PNG file.
        :return: Base64 encoded string of the PNG file.
        """
        with open(png_path, "rb") as png_file:
            png_data = png_file.read()
            return base64.b64encode(png_data).decode('ascii')