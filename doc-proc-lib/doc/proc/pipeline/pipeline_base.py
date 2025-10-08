from abc import abstractmethod
from datetime import datetime, timezone
import os
import traceback
import asyncio
from typing import List, Literal, Optional, Any, Dict
from pydantic import BaseModel
import logging

from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepConfig, StepInstanceConfig
from doc.proc.step.step_instance_loader import create_step_instance
from doc.proc.step.step_registry import StepRegistry
from doc.proc.service.service_base import ServiceBase
from doc.proc.service.service_config import ServiceConfig, ServiceInstanceConfig
from doc.proc.service.service_instance_loader import create_service_instance
from doc.proc.service.service_registry import ServiceRegistry
from doc.proc.source.source_base import SourceBase
from doc.proc.source.source_config import SourceConfig
from doc.proc.source.source_instance_config import SourceInstanceConfig
from doc.proc.source.source_instance_loader import create_source_instance
from doc.proc.source.source_registry import SourceRegistry
from doc.proc.utils.secure_condition_evaluator import SecureConditionEvaluator
from doc.proc.models import Document, PipelineConfigError, PipelineExecutionError, PipelineInput, DocumentResult, StepExecutionResult, PipelineExecutionResult

logger = logging.getLogger("doc.proc.pipeline")


class PipelineExecutionContext:
    """Context for pipeline execution, can be extended with more attributes as needed."""
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_service(self, service_name: str) -> Optional[ServiceBase]:
        """Get a service by name from the execution context."""
        if not hasattr(self, 'services') or not isinstance(self.services, list):
            return None

        return next((service['instance'] for service in self.services if service['name'] == service_name), None)

    def get_source(self, source_name: str) -> Optional[SourceBase]:
        """Get a source by name from the execution context."""
        if not hasattr(self, 'sources') or not isinstance(self.sources, list):
            return None

        return next((source['instance'] for source in self.sources if source['name'] == source_name), None)


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

    def __init__(self, pipeline_config: PipelineConfig, step_registry: StepRegistry, service_registry: ServiceRegistry=None, source_registry: SourceRegistry=None, **kwargs):
        """
        Initialize the Pipeline instance with the provided configuration.
        !IMPORTANT!
        Do not instantiate this class directly; use the `create` method to ensure proper initialization and validation.
        """

        self.pipeline_config = pipeline_config
        self.step_registry = step_registry
        self.service_registry = service_registry
        self.source_registry = source_registry

        if not self.pipeline_config:
            raise PipelineConfigError("Pipeline configuration cannot be None")

        if not self.step_registry or len(self.step_registry) == 0:
            raise PipelineConfigError("Step registry must be provided and non-empty")

        # Service registry is optional - pipelines can run without services

        self.services: List[ServiceBase] = []
        self.sources: List[SourceBase] = []
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
        if self.pipeline_config.service_instances and self.service_registry:
            await self.__load_services()

        # Load sources if available and validate them
        if self.pipeline_config.source_instances and self.source_registry:
            await self.__load_sources()

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
        """Load services based on the configuration using the service registry."""
        
        logger.debug("Loading services from registry")

        if not self.service_registry or len(self.service_registry) == 0:
            # do not raise an error if no services are registered
            # this allows pipelines to run without services if not needed
            return

        for service_instance_config in self.pipeline_config.service_instances:
            logger.debug(f"Loading pipeline service instance configuration: \"{service_instance_config.name}\" that references service catalog id \"{service_instance_config.service_catalog_id}\"")

            if not isinstance(service_instance_config, ServiceInstanceConfig):
                raise TypeError(f"Service configuration must be an instance of ServiceInstanceConfig, got \"{type(service_instance_config)}\"")

            # Check if we have a cached instance first
            cached_instance = self.service_registry.get_cached_instance(
                service_instance_config.service_catalog_id, 
                service_instance_config.name
            )

            if cached_instance:
                logger.debug(f"Using cached service instance \"{service_instance_config.name}\"")
                service_instance = cached_instance
                # Get service config for test_connection check
                service_config = self.service_registry.get_service_config(service_instance_config.service_catalog_id)
            else:
                # Create new instance using the registry
                try:
                    service_instance = self.service_registry.create_service_instance(
                        service_id=service_instance_config.service_catalog_id,
                        instance_name=service_instance_config.name,
                        instance_settings=service_instance_config.settings
                    )
                    service_config = self.service_registry.get_service_config(service_instance_config.service_catalog_id)
                except ValueError as e:
                    raise PipelineConfigError(f"Service configuration for id \"{service_instance_config.service_catalog_id}\" not found in service registry: {str(e)}")

            if not service_instance:
                raise PipelineConfigError(f"Service instance \"{service_instance_config.name}\" could not be created from registry.")

            logger.debug(f"Service instance \"{service_instance_config.name}\" loaded successfully.")

            if service_config and service_config.test_connection:
                logger.debug(f"Testing connection for service instance \"{service_instance_config.name}\"")
                if not await service_instance.test_connection():
                    raise PipelineConfigError(f"Service instance \"{service_instance_config.name}\" failed to pass the connection test")

                logger.debug(f"Service instance \"{service_instance_config.name}\" connection test passed successfully")

            self.services.append({ "name": service_instance_config.name, 
                                   "catalog_id": service_instance_config.service_catalog_id,
                                   "instance": service_instance 
                                 })


    async def __load_sources(self):
        """Load sources based on the configuration using the source registry."""
        
        logger.debug("Loading sources from registry")

        if not self.source_registry or len(self.source_registry) == 0:
            # do not raise an error if no sources are registered
            # this allows pipelines to run without sources if not needed
            return

        for source_instance_config in self.pipeline_config.source_instances:
            logger.debug(f"Loading pipeline source instance configuration: \"{source_instance_config.name}\" that references source catalog id \"{source_instance_config.source_catalog_id}\"")

            if not isinstance(source_instance_config, SourceInstanceConfig):
                raise TypeError(f"Source configuration must be an instance of SourceInstanceConfig, got \"{type(source_instance_config)}\"")

            # Check if we have a cached instance first
            cached_instance = self.source_registry.get_cached_instance(
                source_instance_config.source_catalog_id, 
                source_instance_config.name
            )

            if cached_instance:
                logger.debug(f"Using cached source instance \"{source_instance_config.name}\"")
                source_instance = cached_instance
            else:
                # Create new instance using the registry
                try:
                    source_instance = self.source_registry.create_source_instance(
                        source_id=source_instance_config.source_catalog_id,
                        instance_name=source_instance_config.name,
                        instance_settings=source_instance_config.settings
                    )
                except ValueError as e:
                    raise PipelineConfigError(f"Source configuration for id \"{source_instance_config.source_catalog_id}\" not found in source registry: {str(e)}")

            if not source_instance:
                raise PipelineConfigError(f"Source instance \"{source_instance_config.name}\" could not be created from registry.")

            logger.debug(f"Source instance \"{source_instance_config.name}\" loaded successfully.")

            if source_instance_config.test_connection:
                logger.debug(f"Testing connection for source instance \"{source_instance_config.name}\"")
                if not await source_instance.test_connection():
                    raise PipelineConfigError(f"Source instance \"{source_instance_config.name}\" failed to pass the connection test")

                logger.debug(f"Source instance \"{source_instance_config.name}\" connection test passed successfully")

            self.sources.append({ "name": source_instance_config.name, 
                                   "catalog_id": source_instance_config.source_catalog_id,
                                   "instance": source_instance 
                                 })


    def __load_pipeline_step_instances(self):
        """Load step instances based on the pipeline configuration using the step registry."""

        logger.debug("Loading pipeline step instances.")

        if not self.pipeline_config.steps or not isinstance(self.pipeline_config.steps, list) or len(self.pipeline_config.steps) == 0:
            raise PipelineConfigError("Pipeline step instances configuration is empty")

        for step_instance_config in self.pipeline_config.steps:
            if not isinstance(step_instance_config, StepInstanceConfig):
                raise TypeError(f"Step instance configuration must be an instance of StepInstanceConfig, got \"{type(step_instance_config)}\"")

            # Check if we have a cached instance first
            cached_instance = self.step_registry.get_cached_instance(
                step_instance_config.step_catalog_id, 
                step_instance_config.name
            )

            if cached_instance:
                logger.debug(f"Using cached step instance \"{step_instance_config.name}\"")
                step_instance = cached_instance
            else:
                # Create new instance using the registry
                try:
                    step_instance = self.step_registry.create_step_instance(
                        step_id=step_instance_config.step_catalog_id,
                        instance_config=step_instance_config
                    )
                except ValueError as e:
                    raise PipelineConfigError(f"Step configuration for id \"{step_instance_config.step_catalog_id}\" not found in step registry: {str(e)}")

            logger.debug(f"Step instance \"{step_instance.name}\" of type {type(step_instance).__name__} loaded successfully. Enabled: {step_instance.enabled}")
            
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
    async def create(pipeline_config: PipelineConfig, step_registry: StepRegistry = None, service_registry: ServiceRegistry = None, source_registry: SourceRegistry = None) -> "Pipeline":
        """Factory method to create a Pipeline instance from configuration."""

        if not pipeline_config:
            raise PipelineConfigError("Pipeline configuration cannot be None")
        
        logger.info(f"Creating pipeline instance of '{pipeline_config.name}' from configuration")

        if not step_registry or len(step_registry) == 0:
            raise PipelineConfigError("Step registry cannot be None or empty")

        pipeline_instance = Pipeline(pipeline_config=pipeline_config, step_registry=step_registry, service_registry=service_registry, source_registry=source_registry)

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

    async def _process_single_document(self, document: Document, context: PipelineExecutionContext) -> DocumentResult:
        """Process a single document through the pipeline steps."""
        document_id = document.id
        logger.debug(f"Starting document processing for document ID: {document_id}")
        
        document_start_time = datetime.now()
        
        # Create input data for this document
        _document_data = document
        
        document_result = DocumentResult(
            document_id=document_id,
            result="NotStarted",
            elapsed_time_secs=0,
            data=_document_data.data,
            summary_data=_document_data.summary_data
        )
        
        for step in self.pipeline_execution_steps:
            logger.debug(f"Executing step: {step.name} (Enabled: {step.enabled})")
            
            step_start_time = datetime.now()
            step_result = StepExecutionResult(step_name=step.name, result="NotStarted", elapsed_time_secs=0)
            
            try:
                # Check if the step is enabled
                if not step.enabled:
                    step_result.result = "Skipped"
                    step_result.reason = "Step is not enabled"
                    step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                    document_result.step_results.append(step_result)
                    logger.debug(f"Document {document_id} - Step {step.name} is skipped as it is not enabled.")
                    continue

                # Evaluate the condition for the step
                if step.condition and not self._evaluate_document_condition(document=_document_data.data, condition=step.condition):
                    step_result.result = "Skipped"
                    step_result.reason = "Condition not met"
                    step_result.elapsed_time_secs = (datetime.now() - step_start_time).total_seconds()
                    document_result.step_results.append(step_result)
                    logger.debug(f"Document {document_id} - Step {step.name} is skipped as condition is not met.")
                    continue

                # Update the context with the current step and document
                context.current_step = step
                context.current_document_id = document_id
                
                # Run the step with the current output data and context
                _document_data = await step.run(_document_data, context=context)
                
                if not isinstance(_document_data, Document):
                    raise TypeError(f"Output data from step {step.name} must be an instance of Document")

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
                    document_result.data = _document_data.data
                    document_result.summary_data = _document_data.summary_data
                    document_result.elapsed_time_secs = (datetime.now() - document_start_time).total_seconds()
                    
                    logger.error(f"Document {document_id} - Processing failed due to step {step.name} error: {str(e)}")
                    return document_result
                
                continue
            
            step_elapsed_time = (datetime.now() - step_start_time).total_seconds()
            logger.debug(f"Document {document_id} - Step {step.name} executed successfully. Elapsed time: {step_elapsed_time:.2f} seconds.")
              
            step_result.result = "Succeeded"
            step_result.elapsed_time_secs = step_elapsed_time
            document_result.step_results.append(step_result)
        
        # Finalize the document result
        elapsed_time_secs = (datetime.now() - document_start_time).total_seconds()
        document_result.result = "Succeeded" if all(step.result == "Succeeded" or step.result == "Skipped" for step in document_result.step_results) else "Failed"
        document_result.elapsed_time_secs = elapsed_time_secs
        document_result.data = _document_data.data
        document_result.summary_data = _document_data.summary_data

        logger.debug(f"Document {document_id} processing completed with result: {document_result.result}. Elapsed time: {elapsed_time_secs:.2f} seconds.")

        return document_result

    async def run(self, input_data: PipelineInput) -> PipelineExecutionResult:
        """Run the pipeline with the given input data, processing documents in parallel."""

        logger.debug(f"Starting pipeline '{self.name}' execution with input data")

        if not self.pipeline_execution_steps:
            logger.error("Pipeline execution steps are not defined. Please check the pipeline configuration.")
            raise PipelineConfigError("No execution steps defined in the pipeline")

        context = PipelineExecutionContext(pipeline=self, services=self.services, sources=self.sources, start_time=datetime.now())

        if not isinstance(input_data, PipelineInput):
            logger.error("Input data must be an instance of PipelineInput")
            raise TypeError("Input data must be an instance of PipelineInput")
        
        start_time = datetime.now(timezone.utc)
        
        pipeline_execution_result = PipelineExecutionResult(
            pipeline_name=self.name, 
            result="NotStarted", 
            elapsed_time_secs=0, 
            document_results=[],
            summary_stats={},
            started_at=start_time.isoformat(),
            completed_at=None
        )

        # Check if input data contains documents for parallel processing
        documents = input_data.documents
        
        if documents and isinstance(documents, list) and len(documents) > 0:
            logger.debug(f"Processing {len(documents)} documents in parallel")

            idx = 0
            # Process all documents in parallel
            document_tasks = []
            for document in documents:
                logger.debug(f"Queuing document {idx+1}/{len(documents)} with ID: {document.id} for processing")
                idx += 1
                # Create a copy of context for each document to avoid shared state issues
                doc_context = PipelineExecutionContext(
                    pipeline=self, 
                    services=self.services, 
                    sources=self.sources,
                    start_time=start_time
                )
                task = self._process_single_document(document, doc_context)
                document_tasks.append(task)
            
            # Execute all document processing tasks in parallel
            document_results = await asyncio.gather(*document_tasks, return_exceptions=True)

            for result in document_results:
                pipeline_execution_result.document_results.append(result)
                        
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
            logger.debug("No documents array found, processing as single input")
            
            document_result = await self._process_single_document(input_data.data, context)
            pipeline_execution_result.document_results.append(document_result)
            pipeline_execution_result.result = document_result.result
            pipeline_execution_result.reason = document_result.reason
            

        # Finalize the pipeline execution result
        completed_time = datetime.now(timezone.utc)
        elapsed_time_secs = (completed_time - start_time).total_seconds()
        pipeline_execution_result.completed_at = completed_time.isoformat()
        pipeline_execution_result.elapsed_time_secs = elapsed_time_secs

        logger.info(f"Pipeline '{self.name}' executed with result: {pipeline_execution_result.result}. Total elapsed time: {elapsed_time_secs:.2f} seconds.")

        return pipeline_execution_result
