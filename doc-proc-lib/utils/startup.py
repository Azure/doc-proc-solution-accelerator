import logging

from dependencies import get_config
from typing import Dict, List

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_base import StepInputOutput
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.source_config import SourceConfig

from connectors import CosmosDBClient

logger = logging.getLogger("doc.proc.startup")

config = get_config()
cosmos = CosmosDBClient(config)

async def load_source_catalog_config(source_catalog_yaml_file: str) -> SourceConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_source_catalog_config_from_file(source_catalog_yaml_file)
    elif source == "cosmos":
        return await load_source_catalog_config_from_cosmos(source_catalog_yaml_file)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_source_catalog_config_from_cosmos(document_id: str) -> SourceConfig:

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id.replace(".yaml", ""))
    yaml = document.get("system_prompt", "")

    try:
        # Load source configuration
        source_catalog = SourceConfig.from_yaml(yaml)
        logger.info(f"Source configuration loaded successfully.")
        logger.debug(f"Source configuration: {source_catalog}")

        return source_catalog
        
    except Exception as e:
        logger.error(f"Error loading source catalog: {e}")

async def load_source_catalog_config_from_file(source_catalog_yaml_file: str) -> SourceConfig:

    # Example usage of SourceConfig
    yaml_str = ''

    with open(source_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load source configuration
        source_catalog = SourceConfig.from_yaml(yaml_str)
        logger.info(f"Source configuration loaded successfully.")
        logger.debug(f"Source configuration: {source_catalog}")

        return source_catalog

    except Exception as e:
        logger.error(f"Error loading source catalog: {e}")

async def load_services_catalog_config(services_catalog_yaml_file: str) -> ServiceConfig:

    logger.info(f"Loading services catalog from: {services_catalog_yaml_file}")

    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_services_catalog_config_from_file(services_catalog_yaml_file)
    elif source == "cosmos":
        return await load_services_catalog_config_from_cosmos(services_catalog_yaml_file)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_services_catalog_config_from_cosmos(document_id: str) -> ServiceConfig:

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id.replace(".yaml", ""))
    yaml = document.get("system_prompt", "")

    try:
        # Load services configuration
        service_catalog = ServiceConfig.from_yaml(yaml)
        logger.info(f"Service configuration loaded successfully.")
        logger.debug(f"Service configuration: {service_catalog}")
        
        return service_catalog
        
    except Exception as e:
        logger.error(f"Error loading service catalog: {e}")

async def load_services_catalog_config_from_file(services_catalog_yaml_file: str) -> ServiceConfig:

    # Example usage of ServiceConfig
    yaml_str = ''

    with open(services_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load services configuration
        service_catalog = ServiceConfig.from_yaml(yaml_str)
        logger.info(f"Service configuration loaded successfully.")
        logger.debug(f"Service configuration: {service_catalog}")
        
        return service_catalog
        
    except Exception as e:
        logger.error(f"Error loading service catalog: {e}")

async def load_step_catalog_config(step_catalog_yaml_file: str) -> StepConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_step_catalog_config_from_file(step_catalog_yaml_file)
    elif source == "cosmos":
        return await load_step_catalog_config_from_cosmos(step_catalog_yaml_file)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_step_catalog_config_from_cosmos(document_id: str) -> StepConfig:

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id.replace(".yaml", ""))
    yaml = document.get("system_prompt", "")

    try:
        # Load steps configuration
        step_catalog = StepConfig.from_yaml(yaml)
        logger.info(f"Step configuration loaded successfully.")
        logger.debug(f"Step configuration: {step_catalog}")

        return step_catalog

    except Exception as e:
        logger.error(f"Error loading step catalog: {e}")

async def load_step_catalog_config_from_file(step_catalog_yaml_file: str) -> StepConfig:

    # Example usage of ServiceConfig
    yaml_str = ''

    with open(step_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load steps configuration
        step_catalog = StepConfig.from_yaml(yaml_str)
        logger.info(f"Step configuration loaded successfully.")
        logger.debug(f"Step configuration: {step_catalog}")

        return step_catalog

    except Exception as e:
        logger.error(f"Error loading step catalog: {e}")

async def load_pipeline_config(pipeline_config_yaml_file: str, 
                               step_catalog_config: List[StepConfig] = None, 
                               service_catalog_config: List[ServiceConfig] = None, 
                               source_catalog_config: List[SourceConfig] = None) -> PipelineConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_pipeline_config_from_file(pipeline_config_yaml_file, step_catalog_config, service_catalog_config, source_catalog_config)
    elif source == "cosmos":
        return await load_pipeline_config_from_cosmos(pipeline_config_yaml_file, step_catalog_config, service_catalog_config, source_catalog_config)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_pipeline_config_from_cosmos(document_id: str, step_catalog_config: List[StepConfig] = None, service_catalog_config: List[ServiceConfig] = None, source_catalog_config: List[SourceConfig] = None) -> PipelineConfig:
    """Load pipeline configuration from a YAML file."""

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id.replace(".yaml", ""))
    yaml = document.get("system_prompt", "")

    try:
        # Load pipeline configuration
        pipeline_config = PipelineConfig.from_yaml(yaml, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)
        logger.info(f"Pipeline configuration loaded successfully.")
        logger.debug(f"Pipeline configuration: {pipeline_config}")

        return pipeline_config

    except Exception as e:
        logger.error(f"Error loading pipeline configuration: {e}")


async def load_pipeline_config_from_file(pipeline_config_yaml_file: str, 
                                         step_catalog_config: List[StepConfig] = None, 
                                         service_catalog_config: List[ServiceConfig] = None,
                                         source_catalog_config: List[SourceConfig] = None) -> PipelineConfig:
    """Load pipeline configuration from a YAML file."""
    
    yaml_str = ''

    with open(pipeline_config_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load pipeline configuration
        pipeline_config = PipelineConfig.from_yaml(yaml_str, 
                                                   step_catalog_config=step_catalog_config, 
                                                   service_catalog_config=service_catalog_config,
                                                   source_catalog_config=source_catalog_config)
        logger.info(f"Pipeline configuration loaded successfully.")
        logger.debug(f"Pipeline configuration: {pipeline_config}")

        return pipeline_config

    except Exception as e:
        logger.error(f"Error loading pipeline configuration: {e}")


async def load_pipeline(pipeline_config: PipelineConfig, 
                        step_catalog_config: List[StepConfig] = None, 
                        service_catalog_config: List[ServiceConfig] = None, 
                        source_catalog_config: List[SourceConfig] = None) -> "Pipeline":
    """Load pipeline from configuration."""
    
    if not pipeline_config:
        raise ValueError("Pipeline configuration cannot be None or empty.")

    if not isinstance(pipeline_config, PipelineConfig):
        raise TypeError(f"Expected PipelineConfig instance, got {type(pipeline_config)}")

    # Create the pipeline instance
    pipeline = await Pipeline.create(pipeline_config=pipeline_config,
                                     step_catalog_config=step_catalog_config,
                                     service_catalog_config=service_catalog_config,
                                     source_catalog_config=source_catalog_config
                                    )

    logger.info(f"Pipeline '{pipeline.name}' loaded successfully with {len(pipeline.pipeline_execution_steps)} execution steps.")
    
    return pipeline