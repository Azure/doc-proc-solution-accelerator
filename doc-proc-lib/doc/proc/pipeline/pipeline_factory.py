"""
Pipeline factory utilities for source registry integration.

This module provides convenient factory functions and utilities for creating
pipelines with source registries, following best practices.
"""

import logging
from pathlib import Path
from typing import List, Optional

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_config import StepConfig
from doc.proc.step.step_registry import StepRegistry
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.service_registry import ServiceRegistry
from doc.proc.source.source_config import SourceConfig
from doc.proc.source.source_registry import SourceRegistry
from doc.proc.models import PipelineConfigError

logger = logging.getLogger("doc.proc.pipeline.factory")


class PipelineFactory:
    """Factory for creating pipelines with proper source registry integration."""
    
    def __init__(self, 
                 step_catalog_path: Optional[str] = None,
                 service_catalog_path: Optional[str] = None,
                 source_catalog_path: Optional[str] = None,
                 step_catalog_config: Optional[List[StepConfig]] = None,
                 service_catalog_config: Optional[List[ServiceConfig]] = None,
                 source_catalog_config: Optional[List[SourceConfig]] = None):
        """
        Initialize the pipeline factory with catalog configurations.
        
        Args:
            step_catalog_path: Path to step catalog YAML file
            service_catalog_path: Path to service catalog YAML file  
            source_catalog_path: Path to source catalog YAML file
            step_catalog_config: List of StepConfig objects (alternative to file path)
            service_catalog_config: List of ServiceConfig objects (alternative to file path)
            source_catalog_config: List of SourceConfig objects (alternative to file path)
        """
        self.step_registry = StepRegistry()
        self.service_registry = ServiceRegistry()
        self.source_registry = SourceRegistry()
        
        # Load from provided config objects first (takes priority)
        if step_catalog_config:
            self.load_step_catalog_from_config(step_catalog_config)
        elif step_catalog_path:
            self.load_step_catalog(step_catalog_path)
        
        if service_catalog_config:
            self.load_service_catalog_from_config(service_catalog_config)
        elif service_catalog_path:
            self.load_service_catalog(service_catalog_path)
            
        if source_catalog_config:
            self.load_source_catalog_from_config(source_catalog_config)
        elif source_catalog_path:
            self.load_source_catalog(source_catalog_path)
    
    def load_step_catalog(self, file_path: str) -> None:
        """Load step catalog into registry."""
        try:
            self.step_registry.load_from_yaml(file_path)
            logger.debug(f"Loaded step catalog from {file_path} into registry")
            
        except Exception as e:
            logger.error(f"Failed to load step catalog from {file_path}: {e}")
            raise PipelineConfigError(f"Could not load step catalog: {e}")
    
    def load_service_catalog(self, file_path: str) -> None:
        """Load service catalog into registry."""
        try:
            self.service_registry.load_from_yaml(file_path)
            logger.debug(f"Loaded service catalog from {file_path} into registry")
            
        except Exception as e:
            logger.error(f"Failed to load service catalog from {file_path}: {e}")
            raise PipelineConfigError(f"Could not load service catalog: {e}")
    
    def load_source_catalog(self, file_path: str) -> None:
        """Load source catalog into registry."""
        try:
            self.source_registry.load_from_yaml(file_path)
            logger.debug(f"Loaded source catalog from {file_path} into registry")
            
        except Exception as e:
            logger.error(f"Failed to load source catalog from {file_path}: {e}")
            raise PipelineConfigError(f"Could not load source catalog: {e}")
    
    def load_step_catalog_from_config(self, step_configs: List[StepConfig]) -> None:
        """Load step catalog from a list of StepConfig objects."""
        try:
            from doc.proc.step.step_config import StepConfig
            
            # Clear existing registry
            self.step_registry = StepRegistry()
            
            # Register each step configuration
            for step_config in step_configs:
                if isinstance(step_config, StepConfig):
                    self.step_registry.register_step(step_config)
                else:
                    raise TypeError(f"Expected StepConfig object, got {type(step_config)}")
                    
            logger.debug(f"Loaded {len(step_configs)} step configurations from provided config list")
            
        except Exception as e:
            logger.error(f"Failed to load step catalog from config list: {e}")
            raise PipelineConfigError(f"Could not load step catalog from config: {e}")
    
    def load_service_catalog_from_config(self, service_configs: List[ServiceConfig]) -> None:
        """Load service catalog from a list of ServiceConfig objects."""
        try:
            from doc.proc.service.service_config import ServiceConfig
            
            # Clear existing registry
            self.service_registry = ServiceRegistry()
            
            # Register each service configuration
            for service_config in service_configs:
                if isinstance(service_config, ServiceConfig):
                    self.service_registry.register_service(service_config)
                else:
                    raise TypeError(f"Expected ServiceConfig object, got {type(service_config)}")
                    
            logger.debug(f"Loaded {len(service_configs)} service configurations from provided config list")
            
        except Exception as e:
            logger.error(f"Failed to load service catalog from config list: {e}")
            raise PipelineConfigError(f"Could not load service catalog from config: {e}")
    
    def load_source_catalog_from_config(self, source_configs: List[SourceConfig]) -> None:
        """Load source catalog from a list of SourceConfig objects."""
        try:
            from doc.proc.source.source_config import SourceConfig
            
            # Clear existing registry
            self.source_registry = SourceRegistry()
            
            # Register each source configuration
            for source_config in source_configs:
                if isinstance(source_config, SourceConfig):
                    self.source_registry.register_source(source_config)
                else:
                    raise TypeError(f"Expected SourceConfig object, got {type(source_config)}")
                    
            logger.debug(f"Loaded {len(source_configs)} source configurations from provided config list")
            
        except Exception as e:
            logger.error(f"Failed to load source catalog from config list: {e}")
            raise PipelineConfigError(f"Could not load source catalog from config: {e}")
    
    def register_source(self, source_config) -> None:
        """Register a single source configuration."""
        self.source_registry.register_source(source_config)
    
    def register_step(self, step_config: StepConfig) -> None:
        """Register a single step configuration."""
        self.step_registry.register_step(step_config)
    
    def register_service(self, service_config: ServiceConfig) -> None:
        """Register a single service configuration."""
        self.service_registry.register_service(service_config)
    
    def extend_step_catalog(self, step_configs: List[StepConfig]) -> None:
        """Extend the step catalog with multiple configurations."""
        for step_config in step_configs:
            self.step_registry.register_step(step_config)
        logger.info(f"Extended step catalog with {len(step_configs)} configurations. Total: {len(self.step_registry)}")
    
    def extend_service_catalog(self, service_configs: List[ServiceConfig]) -> None:
        """Extend the service catalog with multiple configurations."""
        for service_config in service_configs:
            self.service_registry.register_service(service_config)
        logger.info(f"Extended service catalog with {len(service_configs)} configurations. Total: {len(self.service_registry)}")
    
    def extend_source_catalog(self, source_configs: List[SourceConfig]) -> None:
        """Extend the source catalog with multiple configurations."""
        for source_config in source_configs:
            self.source_registry.register_source(source_config)
        logger.info(f"Extended source catalog with {len(source_configs)} configurations. Total: {len(self.source_registry)}")
    
    def clear_catalogs(self) -> None:
        """Clear all catalog configurations."""
        self.step_registry.clear_cache()
        self.step_registry = StepRegistry()
        self.service_registry.clear_cache()
        self.service_registry = ServiceRegistry()
        self.source_registry.clear_cache()
        self.source_registry = SourceRegistry()
        logger.info("Cleared all catalog configurations")
    
    def get_step_config(self, step_id: str) -> Optional[StepConfig]:
        """Get a step configuration by ID."""
        return self.step_registry.get_step_config(step_id)
    
    def get_service_config(self, service_id: str) -> Optional[ServiceConfig]:
        """Get a service configuration by ID."""
        return self.service_registry.get_service_config(service_id)
    
    def list_step_ids(self) -> List[str]:
        """Get list of available step IDs."""
        return self.step_registry.list_step_ids()
    
    def list_service_ids(self) -> List[str]:
        """Get list of available service IDs."""
        return self.service_registry.list_service_ids()
    
    def validate_pipeline_config(self, pipeline_config: PipelineConfig) -> List[str]:
        """
        Validate pipeline configuration against available catalogs.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate step references
        for step_instance in pipeline_config.steps or []:
            if not self.step_registry.get_step_config(step_instance.step_catalog_id):
                errors.append(f"Step catalog ID not found: {step_instance.step_catalog_id}")
        
        # Validate service references  
        for service_instance in pipeline_config.service_instances or []:
            if not self.service_registry.get_service_config(service_instance.service_catalog_id):
                errors.append(f"Service catalog ID not found: {service_instance.service_catalog_id}")
        
        # Validate source references
        for source_instance in pipeline_config.source_instances or []:
            if not self.source_registry.get_source_config(source_instance.source_catalog_id):
                errors.append(f"Source catalog ID not found: {source_instance.source_catalog_id}")
        
        # Validate execution sequence
        step_names = {step.name for step in pipeline_config.steps or []}
        for step_name in pipeline_config.execution_sequence or []:
            if step_name not in step_names:
                errors.append(f"Execution sequence references unknown step: {step_name}")
        
        return errors
    
    async def create_pipeline(self, 
                              pipeline_config: PipelineConfig, 
                              validate_config: bool = True) -> Pipeline:
        """
        Create a pipeline using the factory's configured catalogs and registry.
        
        Args:
            pipeline_config: Pipeline configuration
            validate_config: Whether to validate config against catalogs (default: True)
            
        Returns:
            Pipeline: Created and initialized pipeline instance
            
        Raises:
            PipelineConfigError: If validation fails and validate_config is True
        """
        logger.debug(f"Creating pipeline '{pipeline_config.name}' using factory")
        
        # Validate configuration if requested
        if validate_config:
            validation_errors = self.validate_pipeline_config(pipeline_config)
            if validation_errors:
                error_msg = f"Pipeline configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
                logger.error(error_msg)
                raise PipelineConfigError(error_msg)
        
        return await Pipeline.create(
            pipeline_config=pipeline_config,
            step_registry=self.step_registry,
            service_registry=self.service_registry,
            source_registry=self.source_registry
        )
    
    def get_available_sources(self, source_type: Optional[str] = None) -> List[SourceConfig]:
        """Get available sources, optionally filtered by type."""
        if source_type:
            return self.source_registry.get_sources_by_type(source_type)
        return self.source_registry.list_sources()
    
    def get_source_ids(self) -> List[str]:
        """Get list of available source IDs."""
        return self.source_registry.list_source_ids()
    
    def create_source_instance(self, source_id: str, instance_name: str, settings: dict = None):
        """Create a source instance using the registry."""
        return self.source_registry.create_source_instance(source_id, instance_name, settings)
    
    def get_available_steps(self, category: Optional[str] = None) -> List[StepConfig]:
        """Get available steps, optionally filtered by category."""
        if category:
            return self.step_registry.get_steps_by_category(category)
        return self.step_registry.list_steps()
    
    def create_step_instance(self, step_id: str, instance_config):
        """Create a step instance using the registry."""
        return self.step_registry.create_step_instance(step_id, instance_config)
    
    def get_available_services(self, service_type: Optional[str] = None) -> List[ServiceConfig]:
        """Get available services, optionally filtered by type."""
        if service_type:
            return self.service_registry.get_services_by_type(service_type)
        return self.service_registry.list_services()
    
    def create_service_instance(self, service_id: str, instance_name: str, settings: dict = None):
        """Create a service instance using the registry."""
        return self.service_registry.create_service_instance(service_id, instance_name, settings)


async def create_pipeline_from_files(
    pipeline_name: str,
    pipeline_config_path: str = "pipeline_config.yaml",
    step_catalog_path: str = "step_catalog.yaml",
    service_catalog_path: str = "service_catalog.yaml", 
    source_catalog_path: str = "source_catalog.yaml"
) -> Pipeline:
    """
    Convenience function to create a pipeline from catalog yaml files.
    
    Args:
        pipeline_config: Pipeline configuration
        step_catalog_path: Path to step catalog (default: "step_catalog.yaml")
        service_catalog_path: Path to service catalog (default: "service_catalog.yaml")
        source_catalog_path: Path to source catalog (default: "source_catalog.yaml")
        
    Returns:
        Pipeline: Created and initialized pipeline instance
    """
    factory = PipelineFactory()
    
    # Load catalogs if files exist
    for catalog_path, load_method in [
        (step_catalog_path, factory.load_step_catalog),
        (service_catalog_path, factory.load_service_catalog),
        (source_catalog_path, factory.load_source_catalog)
    ]:
        if catalog_path and Path(catalog_path).exists():
            load_method(catalog_path)
        else:
            logger.warning(f"Catalog file not found: {catalog_path}")
    
    with open(pipeline_config_path, 'r') as file:
        pipeline_yaml_str = file.read()


    pipeline_config = PipelineConfig.from_yaml(pipeline_yaml_str, 
                                               step_catalog_config=factory.get_available_steps(), 
                                               service_catalog_config=factory.get_available_services(),
                                               source_catalog_config=factory.get_available_sources())

    _pipeline_config_for_pipeline = next((pipeline for pipeline in pipeline_config if pipeline.name == pipeline_name), None)
    if not _pipeline_config_for_pipeline:
        raise ValueError(f"Pipeline with name '{pipeline_name}' not found in pipeline configuration.")
    
    return await factory.create_pipeline(pipeline_config=_pipeline_config_for_pipeline)


async def create_pipeline_from_configs(
    pipeline_config: PipelineConfig,
    step_catalog_config: List[StepConfig],
    service_catalog_config: Optional[List[ServiceConfig]] = None,
    source_catalog_config: Optional[List[SourceConfig]] = None
) -> Pipeline:
    """
    Create a pipeline from provided configurations.
    
    Args:
        pipeline_config: Pipeline configuration
        step_catalog_config: List of StepConfig objects
        service_catalog_config: Optional list of ServiceConfig objects
        source_catalog_config: Optional list of SourceConfig objects
        
    Returns:
        Pipeline: Created and initialized pipeline instance
    """
    factory = PipelineFactory(
        step_catalog_config=step_catalog_config,
        service_catalog_config=service_catalog_config,
        source_catalog_config=source_catalog_config
    )
    
    return await factory.create_pipeline(pipeline_config)

