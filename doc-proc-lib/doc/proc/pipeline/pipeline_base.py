from abc import abstractmethod
from datetime import datetime
import os
import traceback
import asyncio
from typing import List, Literal, Optional, Any, Dict
from pydantic import BaseModel
import logging

from doc.proc.pipeline.pipeline_config import PipelineConfig, ServiceInstanceConfig
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_base import ServiceBase
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.service_instance_loader import create_service_instance
from doc.proc.step.step_instance_loader import create_step_instance
from doc.proc.utils.secure_condition_evaluator import SecureConditionEvaluator

logger = logging.getLogger("doc.proc.pipeline")


class StepExecutionResult(BaseModel):
    """Model for the result of a step execution."""
    step_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "Skipped"] = "NotStarted"
    reason: Optional[str] = None  # Reason for skipping or failure, if applicable
    elapsed_time_secs: float
    error: Optional[str] = None  # Error message if the step fails
    error_message: Optional[str] = None  # Detailed error message if available
    error_traceback: Optional[str] = None  # Traceback of the error if available


class DocumentResult(BaseModel):
    """Model for the result of processing a single document."""
    document_id: str
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None  # Reason for failure or partial success, if applicable
    elapsed_time_secs: float
    data: Dict[str, Any] = {}  # Final data output from document processing
    summary_data: Dict[str, Any] = {}  # Summary data for document processing
    step_results: List[StepExecutionResult] = []  # List of StepExecutionResult for each step
    

class PipelineExecutionResult(BaseModel):
    """Model for the output of a pipeline execution."""
    pipeline_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None  # Reason for failure or partial success, if applicable
    elapsed_time_secs: float
    document_results: List[DocumentResult] = []  # List of DocumentResult for each document processed
    summary_stats: dict = {}  # Summary statistics for the pipeline execution


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

        self.services: List[ServiceBase] = []
        self.pipeline_step_instances: List[StepBase] = []
        self.pipeline_execution_steps: List[StepBase] = []

        self.condition_evaluator = SecureConditionEvaluator()

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

            service_instance = create_service_instance(
                service_config=service_config,
                instance_settings=service_instance_config.settings
            )

            if not service_instance:
                raise PipelineConfigError(f"Service instance \"{service_config.name}\" could not be created from configuration in the catalog.")

            logger.debug(f"Service instance \"{service_instance_config.name}\" loaded successfully.")

            if service_config.test_connection:
                logger.debug(f"Testing connection for service instance \"{service_instance_config.name}\"")
                if not await service_instance.test_connection():
                    raise PipelineConfigError(f"Service instance \"{service_instance_config.name}\" failed to pass the connection test")

                logger.debug(f"Service instance \"{service_instance_config.name}\" connection test passed successfully")

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

            logger.debug(f"Loading step instance \"{step_instance_config.name}\" of type {step_config.class_name}.")

            # Initialize the step with the instance configuration
            step_instance = create_step_instance(step_config=step_config, step_instance_config=step_instance_config)
            
            logger.debug(f"Step instance \"{step_instance.name}\" of type {type(step_instance).__name__} created successfully. Enabled: {step_instance.enabled}")
            
            self.pipeline_step_instances.append(step_instance)


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

        if not pipeline_config:
            raise PipelineConfigError("Pipeline configuration cannot be None")
        
        logger.info(f"Creating pipeline instance of '{pipeline_config.name}' from configuration")

        if not step_catalog_config or len(step_catalog_config) == 0:
            raise PipelineConfigError("Step catalog cannot be None or empty")

        pipeline_instance = Pipeline(pipeline_config=pipeline_config, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)

        # Load and validate the pipeline configuration and steps.
        try:
            await pipeline_instance.__load()
        except Exception as e:
            raise PipelineConfigError(f"Error loading pipeline from configuration: {str(e)}")

        logger.info(f"Pipeline instance '{pipeline_instance.name}' created successfully with {len(pipeline_instance.pipeline_execution_steps)} execution steps.")
        return pipeline_instance

    def _evaluate_document_condition(self, document: dict, condition: str) -> bool:
        """
        Evaluate a step's condition against a specific document.
        
        Args:
            document: The document to evaluate the condition against
            condition: The condition to evaluate

        Returns:
            bool: True if the condition is met or no condition is set, False otherwise
            
        Raises:
            Exception: If condition evaluation fails
        """
        if not document or not condition or not self.condition_evaluator:
            return True  # No condition means always process
        
        try:
            # Create evaluation context with document data
            evaluation_data = {}

            logger.debug(f"Evaluating condition {condition} for document {document}")

            # Add document data to evaluation context
            evaluation_data.update(document)
            
            # Evaluate the condition
            condition_group = self.condition_evaluator.parse_condition_string(condition)
            logger.debug(f"Evaluation condition group: {condition_group}")
            result = self.condition_evaluator.evaluate(condition_group, evaluation_data)
            logger.debug(f"Condition evaluation result for document: {result}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating condition for document: {e}")
            raise Exception(f"Failed to evaluate condition '{condition}': {str(e)}")

    async def _process_single_document(self, document_data: dict, context: PipelineExecutionContext) -> DocumentResult:
        """Process a single document through the pipeline steps."""
        document_id = document_data.get('id', document_data.get('id', document_data.get('blob_name', 'unknown')))
        logger.info(f"Starting document processing for document ID: {document_id}")
        
        document_start_time = datetime.now()
        
        # Create input data for this document
        input_data = StepInputOutput(id=document_id, data=document_data, summary_data={})
        output_data = input_data
        
        document_result = DocumentResult(
            document_id=document_id,
            result="NotStarted",
            elapsed_time_secs=0,
            data=output_data.data,
            summary_data=output_data.summary_data
        )
        
        for step in self.pipeline_execution_steps:
            logger.debug(f"Processing document {document_id} - Executing step: {step.name} (Enabled: {step.enabled})")
            
            step_start_time = datetime.now()
            step_result = StepExecutionResult(step_name=step.name, result="NotStarted", elapsed_time_secs=0)
            
            try:
                # Check if the step is enabled
                if not step.enabled:
                    step_result.result = "Skipped"
                    step_result.reason = "Step is not enabled"
                    step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                    document_result.step_results.append(step_result)
                    logger.info(f"Document {document_id} - Step {step.name} is skipped as it is not enabled.")
                    continue

                # Evaluate the condition for the step
                if step.condition and not self._evaluate_document_condition(document=output_data.data, condition=step.condition):
                    step_result.result = "Skipped"
                    step_result.reason = "Condition not met"
                    step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                    document_result.step_results.append(step_result)
                    logger.info(f"Document {document_id} - Step {step.name} is skipped as condition is not met.")
                    continue

                # Update the context with the current step and document
                context.current_step = step
                context.current_document_id = document_id
                
                # Run the step with the current output data and context
                output_data = await step.run(output_data, context=context)
                if not isinstance(output_data, StepInputOutput):
                    raise TypeError(f"Output data from step {step.name} must be an instance of StepInputOutput")
                
            except Exception as e:
                logger.error(f"Document {document_id} - Error executing step {step.name}: {str(e)}")
                
                step_result.result = "Failed"
                step_result.reason = f"Error executing step: {str(e)}"
                step_result.error = str(e)
                step_result.error_message = str(e)
                step_result.error_traceback = traceback.format_exc()
                step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                document_result.step_results.append(step_result)
                
                if step.fail_pipeline_on_error:
                    document_result.result = "Failed"
                    document_result.reason = f"Document processing failed due to step {step.name} error: {str(e)}"
                    document_result.data = output_data.data
                    document_result.summary_data = output_data.summary_data
                    document_result.elapsed_time_secs = (datetime.now() - document_start_time).total_seconds()
                    
                    logger.error(f"Document {document_id} - Processing failed due to step {step.name} error: {str(e)}")
                    return document_result
                
                continue
            
            step_elapsed_time = (datetime.now() - step_start_time).total_seconds()
            logger.info(f"Document {document_id} - Step {step.name} executed successfully. Elapsed time: {step_elapsed_time:.2f} seconds.")
            
            if step.debug_mode:
                logger.debug(f"Document {document_id} - Step {step.name} output data: {output_data.data}")
            
            step_result.result = "Succeeded"
            step_result.elapsed_time_secs = step_elapsed_time
            document_result.step_results.append(step_result)
        
        # Finalize the document result
        elapsed_time_secs = (datetime.now() - document_start_time).total_seconds()
        document_result.result = "Succeeded" if all(step.result == "Succeeded" or step.result == "Skipped" for step in document_result.step_results) else "Failed"
        document_result.elapsed_time_secs = elapsed_time_secs
        document_result.data = output_data.data
        document_result.summary_data = output_data.summary_data
        
        logger.info(f"Document {document_id} processing completed with result: {document_result.result}. Elapsed time: {elapsed_time_secs:.2f} seconds.")
        
        return document_result

    async def run(self, input_data: StepInputOutput) -> PipelineExecutionResult:
        """Run the pipeline with the given input data, processing documents in parallel."""

        logger.info(f"Starting pipeline '{self.name}' execution with input data")

        if not self.pipeline_execution_steps:
            logger.error("Pipeline execution steps are not defined. Please check the pipeline configuration.")
            raise PipelineConfigError("No execution steps defined in the pipeline")

        context = PipelineExecutionContext(pipeline=self, services=self.services, start_time=datetime.now())

        if not isinstance(input_data, StepInputOutput):
            logger.error("Input data must be an instance of StepInputOutput")
            raise TypeError("Input data must be an instance of StepInputOutput")
        
        pipeline_execution_result = PipelineExecutionResult(
            pipeline_name=self.name, 
            result="NotStarted", 
            elapsed_time_secs=0, 
            document_results=[],
            summary_stats={}
        )

        # Check if input data contains documents for parallel processing
        documents = input_data.data.get('documents', [])
        
        if documents and isinstance(documents, list) and len(documents) > 0:
            logger.info(f"Processing {len(documents)} documents in parallel")
            
            # Process all documents in parallel
            document_tasks = []
            for document in documents:
                # Create a copy of context for each document to avoid shared state issues
                doc_context = PipelineExecutionContext(
                    pipeline=self, 
                    services=self.services, 
                    start_time=datetime.now()
                )
                task = self._process_single_document(document, doc_context)
                document_tasks.append(task)
            
            # Execute all document processing tasks in parallel
            document_results = await asyncio.gather(*document_tasks, return_exceptions=True)
            print(document_results)
            # Process results and handle any exceptions
            # for i, result in enumerate(document_results):
            for result in document_results:
                
                # if isinstance(result, Exception):
                #     logger.error(f"Document {i} processing failed with exception: {str(result)}")
                #     # Create a failed document result for exceptions
                #     failed_result = DocumentResult(
                #         document_id=f"document_{i}",
                #         result="Failed",
                #         reason=f"Document processing failed with exception: {str(result)}",
                #         elapsed_time_secs=0,
                #         step_results=[]
                #     )
                #     pipeline_execution_result.document_results.append(failed_result)
                # else:
                pipeline_execution_result.document_results.append(result)
            
            # # Aggregate step execution results from all document results
            # step_aggregation = {}
            # for doc_result in pipeline_execution_result.document_results:
            #     for step_result in doc_result.step_results:
            #         if step_result.step_name not in step_aggregation:
            #             step_aggregation[step_result.step_name] = {
            #                 "succeeded": 0,
            #                 "failed": 0,
            #                 "skipped": 0,
            #                 "total_time": 0,
            #                 "errors": []
            #             }
                    
            #         step_agg = step_aggregation[step_result.step_name]
            #         step_agg["total_time"] += step_result.elapsed_time_secs
                    
            #         if step_result.result == "Succeeded":
            #             step_agg["succeeded"] += 1
            #         elif step_result.result == "Failed":
            #             step_agg["failed"] += 1
            #             if step_result.error:
            #                 step_agg["errors"].append(step_result.error)
            #         elif step_result.result == "Skipped":
            #             step_agg["skipped"] += 1
            
            # # Create aggregated step execution results
            # for step_name, agg_data in step_aggregation.items():
            #     total_docs = len(pipeline_execution_result.document_results)
            #     avg_time = agg_data["total_time"] / total_docs if total_docs > 0 else 0
                
            #     # Determine overall step result
            #     if agg_data["failed"] > 0:
            #         step_status = "Failed" if agg_data["succeeded"] == 0 else "PartialSucceeded"
            #         reason = f"{agg_data['failed']} out of {total_docs} documents failed"
            #     elif agg_data["succeeded"] > 0:
            #         step_status = "Succeeded"
            #         reason = f"All {agg_data['succeeded']} documents succeeded"
            #     else:
            #         step_status = "Skipped" 
            #         reason = f"Step skipped for all {total_docs} documents"
                
            #     aggregated_step_result = StepExecutionResult(
            #         step_name=step_name,
            #         result=step_status,
            #         reason=reason,
            #         elapsed_time_secs=avg_time
            #     )
                
            #     if agg_data["errors"]:
            #         aggregated_step_result.error = f"Errors occurred in {len(agg_data['errors'])} documents"
            #         aggregated_step_result.error_message = "; ".join(set(agg_data["errors"][:5]))  # Limit to first 5 unique errors
                
            #     pipeline_execution_result.step_execution_results.append(aggregated_step_result)
            print(pipeline_execution_result)
            
            # Determine overall pipeline result
            successful_docs = len([dr for dr in pipeline_execution_result.document_results if dr.result == "Succeeded"])
            failed_docs = len([dr for dr in pipeline_execution_result.document_results if dr.result == "Failed"])
            total_docs = len(pipeline_execution_result.document_results)
            
            if successful_docs == total_docs:
                pipeline_execution_result.result = "Succeeded"
                pipeline_execution_result.reason = f"All {total_docs} documents processed successfully"
            elif successful_docs > 0:
                pipeline_execution_result.result = "PartialSucceeded"
                pipeline_execution_result.reason = f"{successful_docs} out of {total_docs} documents processed successfully"
            else:
                pipeline_execution_result.result = "Failed"
                pipeline_execution_result.reason = f"All {total_docs} documents failed to process"
            
            # Set aggregated data
            pipeline_execution_result.summary_stats = {
                "total_documents": total_docs,
                "successful_documents": successful_docs,
                "failed_documents": failed_docs,
                "success_rate": (successful_docs / total_docs * 100) if total_docs > 0 else 0
            }
            
        else:
            # Fallback to single document processing
            logger.info("No documents array found, processing as single input")
            
            document_result = await self._process_single_document(input_data.data, context)
            pipeline_execution_result.document_results.append(document_result)
            pipeline_execution_result.result = document_result.result
            pipeline_execution_result.reason = document_result.reason
            

        # Finalize the pipeline execution result
        elapsed_time_secs = (datetime.now() - context.start_time).total_seconds()
        pipeline_execution_result.elapsed_time_secs = elapsed_time_secs

        logger.info(f"Pipeline '{self.name}' executed with result: {pipeline_execution_result.result}. Total elapsed time: {elapsed_time_secs:.2f} seconds.")

        return pipeline_execution_result
