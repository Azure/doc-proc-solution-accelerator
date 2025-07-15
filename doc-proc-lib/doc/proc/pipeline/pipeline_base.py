from abc import abstractmethod
from datetime import datetime
import os
from typing import List, Literal, Optional
from pydantic import BaseModel
import logging

from doc.proc.pipeline.pipeline_config import PipelineConfig, ServiceInstanceConfig
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_base import ServiceBase
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.service_manager import get_service
from doc.proc.utils.import_module import import_module
from doc.proc.utils.secure_condition_evaluator import SecureConditionEvaluator, ConditionEvaluationError


logger = logging.getLogger(__name__)


class StepExecutionResult(BaseModel):
    """Model for the result of a step execution."""
    step_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "Skipped"] = "NotStarted"
    reason: Optional[str] = None  # Reason for skipping or failure, if applicable
    elapsed_time_secs: float
    error: Optional[str] = None  # Error message if the step fails
    error_message: Optional[str] = None  # Detailed error message if available
    error_traceback: Optional[str] = None  # Traceback of the error if available
    

class PipelineExecutionResult(BaseModel):
    """Model for the output of a pipeline execution."""
    pipeline_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None  # Reason for failure or partial success, if applicable
    elapsed_time_secs: float
    step_execution_results: List[StepExecutionResult] = []  # List of StepExecutionResult for each step in the pipeline
    summary_data: dict = {}  # Summary data for the pipeline execution
    data: dict = {}  # Final data output from the pipeline execution


class PipelineExecutionContext:
    """Context for pipeline execution, can be extended with more attributes as needed."""
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_service(self, service_name: str) -> Optional[ServiceBase]:
        """Get a service by name from the execution context."""
        if not hasattr(self, 'services') or not isinstance(self.services, list):
            return None

        return next((service['instance'] for service in self.services if service['name'] == service_name), None)


class PipelineExecutionError(Exception):
    """Custom exception for errors during pipeline execution."""
    pass


class PipelineConfigError(Exception):
    """Custom exception for errors in pipeline configuration."""
    pass


class Pipeline:
    """
        Base class for pipeline execution, managing the configuration and steps.
        
        This class is responsible for loading the pipeline configuration, initializing services,
        and executing the steps in the defined sequence.
        It provides methods to create a pipeline instance from configuration and run the pipeline with input data.

        !IMPORTANT!
        Do not instantiate this class directly; use the `create` method to ensure proper initialization and validation.

        Attributes:
            pipeline_config (PipelineConfig): Configuration for the pipeline.
            steps_config (List[StepConfig]): Configuration for steps in the pipeline.
            services_config (List[ServiceConfig]): Configuration for services used in the pipeline.
            
    """

    def __init__(self, pipeline_config: PipelineConfig, step_catalog_config: List[StepConfig], service_catalog_config: List[ServiceConfig]=None, **kwargs):
        """
        Initialize the Pipeline instance with the provided configuration.
        !IMPORTANT!
        Do not instantiate this class directly; use the `create` method to ensure proper initialization and validation.
        """

        self.pipeline_config = pipeline_config
        self.step_catalog = step_catalog_config
        self.service_catalog = service_catalog_config

        if not self.pipeline_config:
            raise PipelineConfigError("Pipeline configuration cannot be None")

        if not self.step_catalog or not isinstance(self.step_catalog, list) or len(self.step_catalog) == 0:
            raise PipelineConfigError("Steps configuration must be a non-empty list")

        if self.service_catalog and not isinstance(self.service_catalog, list) and not len(self.service_catalog) > 0:
            raise PipelineConfigError("Services configuration must be a non-empty list if provided")

        self.condition_evaluator = SecureConditionEvaluator()  # Initialize condition evaluator
        self.services: List[ServiceBase] = []
        self.pipeline_step_instances: List[StepBase] = []
        self.pipeline_execution_steps: List[StepBase] = []
    

    async def __load(self):
        """Load the pipeline configuration and steps."""
       
        self.name = self.pipeline_config.name
        self.description = self.pipeline_config.description
        self.version = self.pipeline_config.version
        self.execution_sequence = self.pipeline_config.execution_sequence
        self.settings = self.pipeline_config.settings

        if not self.name:
            raise PipelineConfigError("Pipeline name cannot be empty")

        if not self.execution_sequence or not isinstance(self.execution_sequence, list):
            raise PipelineConfigError("Pipeline execution sequence cannot be empty and must be a list.")

        # Load services if available and validate them
        if self.pipeline_config.service_instances and self.service_catalog:
            await self.__load_services()

        # Load steps and validate them
        self.__load_pipeline_step_instances()
        if not self.pipeline_step_instances:
            raise PipelineConfigError("No pipeline step instances loaded from the configuration")

        # Load execution steps based on the defined sequence
        self.__load_execution_steps()
        if not self.pipeline_execution_steps:
            raise PipelineConfigError("No execution steps defined in the pipeline execution sequence")

        # Additional validation can be added here if needed


    async def __load_services(self):
        """Load services based on the configuration."""
        
        logger.debug("Loading services from configuration")

        if not self.service_catalog or not isinstance(self.service_catalog, list) or len(self.service_catalog) == 0:
            # do not raise an error if no services are configured
            # this allows pipelines to run without services if not needed
            return

        for service_instance_config in self.pipeline_config.service_instances:
            logger.debug(f"Loading pipeline service instance configuration: \"{service_instance_config.name}\" that references service catalog id \"{service_instance_config.service_catalog_id}\"")

            if not isinstance(service_instance_config, ServiceInstanceConfig):
                raise TypeError(f"Service configuration must be an instance of ServiceInstanceConfig, got \"{type(service_instance_config)}\"")

            service_config = next((s for s in self.service_catalog if s.id == service_instance_config.service_catalog_id), None)
            if not service_config:
                raise PipelineConfigError(f"Service configuration for id \"{service_instance_config.service_catalog_id}\" not found in services catalog.")

            service_instance = await get_service(
                service_config=service_config,
                instance_settings=service_instance_config.settings
            )

            if not service_instance:
                raise PipelineConfigError(f"Service instance \"{service_config.name}\" could not be created from configuration in the catalog.")

            logger.info(f"Service instance \"{service_instance_config.name}\" loaded successfully.")

            if service_config.test_connection:
                logger.debug(f"Testing connection for service instance \"{service_instance_config.name}\"")
                if not await service_instance.test_connection():
                    raise PipelineConfigError(f"Service instance \"{service_instance_config.name}\" failed to pass the connection test")

                logger.info(f"Service instance \"{service_instance_config.name}\" connection test passed successfully")

            self.services.append({ "name": service_instance_config.name, 
                                   "catalog_id": service_instance_config.service_catalog_id,
                                   "instance": service_instance 
                                 })


    def __load_pipeline_step_instances(self):
        """Load step instances based on the pipeline configuration."""

        logger.debug("Loading pipeline step instances.")

        if not self.pipeline_config.steps or not isinstance(self.pipeline_config.steps, list) or len(self.pipeline_config.steps) == 0:
            raise PipelineConfigError("Pipeline step instances configuration is empty")

        for step_instance_config in self.pipeline_config.steps:
            if not isinstance(step_instance_config, StepInstanceConfig):
                raise TypeError(f"Step instance configuration must be an instance of StepInstanceConfig, got \"{type(step_instance_config)}\"")

            step_config = next((s for s in self.step_catalog if s.id == step_instance_config.step_catalog_id), None)
            if not step_config:
                raise PipelineConfigError(f"Step with catalog id \"{step_instance_config.step_catalog_id}\" not found in step catalog configuration.")

            # Initialize the step with the instance configuration
            step_instance = Pipeline.__init_step(step_config=step_config, step_instance_config=step_instance_config)
            
            self.pipeline_step_instances.append(step_instance)


    @staticmethod
    def __init_step(step_config: StepConfig, step_instance_config: StepInstanceConfig) -> StepBase:
        """Load steps based on the configuration."""

        logger.debug(f"Initializing step: \"{step_config.id}\" with instance config: {step_instance_config.name}")

        if not isinstance(step_config, StepConfig):
            raise PipelineConfigError(f"Step configuration must be an instance of StepConfig, got {type(step_config)}")

        if not isinstance(step_instance_config, StepInstanceConfig):
            raise PipelineConfigError(f"Step instance configuration must be an instance of StepInstanceConfig, got {type(step_instance_config)}")

        # Validate the step configuration
        if not step_config.id:
            raise PipelineConfigError("Step configuration must have an id defined")

        module_name = step_config.module_name
        if not module_name:
            raise PipelineConfigError(f"Step \"{step_config.id}\" does not have a module defined")

        module_path = step_config.module_path
        if not module_path:
            raise PipelineConfigError(f"Step \"{step_config.id}\" does not have a module path defined")

        class_name = step_config.class_name
        if not class_name:
            raise PipelineConfigError(f"Step \"{step_config.id}\" does not have a class defined")

        # Import the module dynamically
        logger.debug(f"Importing step module: \"{module_name}\" from path: \"{module_path}\"")

        if not os.path.exists(module_path):
            logger.error(f"Module path \"{module_path}\" does not exist for step \"{step_config.id}\"")
            raise PipelineConfigError(f"Module path \"{module_path}\" does not exist for step \"{step_config.id}\"")

        step_module = import_module(module_path=module_path, module_name=module_name)
        step_class = getattr(step_module, class_name, None)
        if not step_class:
            raise PipelineConfigError(f"Step \"{step_config.id}\" class \"{class_name}\" not found in module \"{module_name}\" at path \"{module_path}\"")

        if not hasattr(step_class, '__call__'):
            raise TypeError(f"{class_name} is not callable or does not have a __call__ method.")


        # Create an instance of the step class with the provided configuration
        step_instance = step_class(instance_config=step_instance_config) 

        if not isinstance(step_instance, StepBase):
            raise TypeError(f"Step \"{step_config.id}\" is not an instance of StepBase")

        logger.info(f"Step instance \"{step_instance.name}\" of type {type(step_instance).__name__} created successfully. Enabled: {step_instance.enabled}")

        return step_instance
    

    def __load_execution_steps(self):
        """Load steps in the order defined by the execution sequence."""
        
        logger.debug("Loading pipeline execution steps based on the execution sequence")

        ordered_steps = []
        for step_name in self.execution_sequence:
            step = next((s for s in self.pipeline_step_instances if s.name == step_name), None)
            if not step:
                raise PipelineConfigError(f"Execution sequence step \"{step_name}\" not found in pipeline steps")

            ordered_steps.append(step)

        self.pipeline_execution_steps = ordered_steps


    @staticmethod
    async def create(pipeline_config: PipelineConfig, step_catalog_config: List[StepConfig] = None, service_catalog_config: List[ServiceConfig] = None) -> "Pipeline":
        """Factory method to create a Pipeline instance from configuration."""
        
        logger.info("Creating pipeline instance from configuration")
        
        if not pipeline_config:
            raise PipelineConfigError("Pipeline configuration cannot be None")

        if not step_catalog_config or len(step_catalog_config) == 0:
            raise PipelineConfigError("Step catalog cannot be None or empty")

        pipeline_instance = Pipeline(pipeline_config=pipeline_config, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)

        # Load and validate the pipeline configuration and steps.
        try:
            await pipeline_instance.__load()
        except Exception as e:
            raise PipelineConfigError(f"Error loading pipeline from configuration: {str(e)}")

        logger.debug(f"Pipeline instance '{pipeline_instance.name}' created successfully with {len(pipeline_instance.pipeline_execution_steps)} execution steps.")
        return pipeline_instance


    async def run(self, input_data: StepInputOutput) -> PipelineExecutionResult:
        """Run the pipeline with the given input data."""

        logger.info(f"Starting pipeline '{self.name}' execution with input data: {input_data.data}")

        if not self.pipeline_execution_steps:
            logger.error("Pipeline execution steps are not defined. Please check the pipeline configuration.")
            raise PipelineConfigError("No execution steps defined in the pipeline")

        context = PipelineExecutionContext(pipeline=self, services=self.services, start_time=datetime.now())

        output_data = input_data

        result_status = "NotStarted"

        if not isinstance(output_data, StepInputOutput):
            logger.error("Input data must be an instance of StepInputOutput")
            raise TypeError("Input data must be an instance of StepInputOutput")
        
        pipeline_execution_result = PipelineExecutionResult(pipeline_name=self.name, result=result_status, elapsed_time_secs=0, data=output_data.data, summary_data=output_data.summary_data)

        for step in self.pipeline_execution_steps:
            
            logger.debug(f"Executing step: {step.name} (Enabled: {step.enabled}, Debug Mode: {step.debug_mode})")

            step_start_time = datetime.now()
            step_result = StepExecutionResult(step_name=step.name, result="NotStarted", elapsed_time_secs=0)

            try:
                # Check if the step is enabled
                if not step.enabled:
                    step_result.result = "Skipped"
                    step_result.reason = "Step is not enabled"
                    step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                    pipeline_execution_result.step_execution_results.append(step_result)
                    logger.info(f"Step {step.name} is skipped as it is not enabled.")
                    continue

                # Evaluate step condition if present
                if step.condition:
                    try:
                        condition_met = self._evaluate_step_condition(step, output_data)
                        if not condition_met:
                            step_result.result = "Skipped"
                            step_result.reason = f"Condition not met: {step.condition}"
                            step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                            pipeline_execution_result.step_execution_results.append(step_result)
                            logger.info(f"Step {step.name} is skipped as condition was not met: {step.condition}")
                            continue
                    
                    except ConditionEvaluationError as ce:
                        logger.error(f"Condition evaluation error for step {step.name}: {ce}")
                        step_result.result = "Failed"
                        step_result.reason = f"Condition evaluation error: {str(ce)}"
                        step_result.error = f"Condition evaluation error: {str(ce)}"
                        step_result.error_message = str(ce)
                        step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                        pipeline_execution_result.step_execution_results.append(step_result)
                        
                        if step.fail_pipeline_on_error == True:
                            pipeline_execution_result.result = "Failed"
                            pipeline_execution_result.reason = f"Pipeline execution failed due to condition evaluation error in step {step.name}"
                            pipeline_execution_result.data = output_data.data
                            pipeline_execution_result.summary_data = output_data.summary_data
                            pipeline_execution_result.elapsed_time_secs = (datetime.now() - context.start_time).total_seconds()
                            logger.error(f"Pipeline execution failed due to condition evaluation error in step {step.name}")
                            return pipeline_execution_result
                        
                        continue

                # Update the context with the current step
                context.current_step = step

                # Run the step with the current output data and context
                output_data = await step.run(output_data, context=context)
                if not isinstance(output_data, StepInputOutput):
                    raise TypeError(f"Output data from step {step.name} must be an instance of StepInputOutput")
                
            except Exception as e:
                logger.error(f"Error executing step {step.name}: {str(e)}")

                step_result.result = "Failed"
                step_result.reason = f"Error executing step: {str(e)}"
                step_result.error = str(e)
                step_result.error_message = str(e)
                step_result.error_traceback = e.__traceback__ if hasattr(e, '__traceback__') else None
                step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                pipeline_execution_result.step_execution_results.append(step_result)

                if step.fail_pipeline_on_error == True:
                    pipeline_execution_result.result = "Failed"
                    pipeline_execution_result.reason = f"Pipeline execution failed due to step {step.name} error: {str(e)}"
                    pipeline_execution_result.data = output_data.data
                    pipeline_execution_result.summary_data = output_data.summary_data
                    pipeline_execution_result.elapsed_time_secs = (datetime.now() - context.start_time).total_seconds()
                    
                    logger.error(f"Pipeline execution failed due to step {step.name} error: {str(e)}")
                    return pipeline_execution_result
                
                continue

            step_elapsed_time = (datetime.now() - step_start_time).total_seconds()
            logger.info(f"Step {step.name} executed successfully. Elapsed time: {step_elapsed_time:.2f} seconds.")
            if step.debug_mode:
                logger.debug(f"Step {step.name} output data: {output_data.data}")
            step_result.result = "Succeeded"
            step_result.elapsed_time_secs = step_elapsed_time
            pipeline_execution_result.step_execution_results.append(step_result)

        # Finalize the pipeline execution result
        elapsed_time_secs = (datetime.now() - context.start_time).total_seconds()
        pipeline_execution_result.result = "Succeeded" if all(step.result == "Succeeded" or step.result == "Skipped" for step in pipeline_execution_result.step_execution_results) else "PartialSucceeded"
        pipeline_execution_result.elapsed_time_secs = elapsed_time_secs
        pipeline_execution_result.data = output_data.data
        pipeline_execution_result.summary_data = output_data.summary_data

        logger.info(f"Pipeline '{self.name}' executed with result: {pipeline_execution_result.result}. Total elapsed time: {elapsed_time_secs:.2f} seconds.")

        return pipeline_execution_result


    def _evaluate_step_condition(self, step: StepBase, input_data: StepInputOutput) -> bool:
        """
        Evaluate a step's condition against the current pipeline data.
        
        Args:
            step: The step to evaluate the condition for
            input_data: The current input data for the step
            
        Returns:
            bool: True if the condition is met or no condition is set, False otherwise
            
        Raises:
            ConditionEvaluationError: If condition evaluation fails
        """
        if not step.condition:
            return True  # No condition means always run
        
        try:
            logger.debug(f"Evaluating condition for step {step.name}: {step.condition}")
            
            # Create evaluation context with current data
            evaluation_data = {}
            
            # Add input data to evaluation context
            if input_data.data:
                evaluation_data.update(input_data.data)
            
            # Add summary data to evaluation context
            if input_data.summary_data:
                evaluation_data.update(input_data.summary_data)
            
            # Evaluate the condition
            condition_group = self.condition_evaluator.parse_condition_string(step.condition)
            result = self.condition_evaluator.evaluate(condition_group, evaluation_data)
            
            logger.debug(f"Condition evaluation result for step {step.name}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating condition for step {step.name}: {e}")
            raise ConditionEvaluationError(f"Failed to evaluate condition '{step.condition}': {str(e)}")
