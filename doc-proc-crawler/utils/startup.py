import logging

from dependencies import get_config
from typing import Dict, List

from app.crawler.crawler_base import Crawler
from app.crawler.crawler_config import CrawlerConfig

from doc.proc.source.source_config import SourceConfig

from connectors import CosmosDBClient

logger = logging.getLogger("doc.proc.crawler.startup")

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

async def load_crawler_config(crawler_config_yaml_file: str,
                               source_catalog_config: List[SourceConfig] = None) -> CrawlerConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_crawler_config_from_file(crawler_config_yaml_file, source_catalog_config)
    elif source == "cosmos":
        return await load_crawler_config_from_cosmos(crawler_config_yaml_file, source_catalog_config)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_crawler_config_from_cosmos(document_id: str, source_catalog_config: List[SourceConfig] = None) -> CrawlerConfig:
    """Load crawler configuration from a YAML file."""

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id.replace(".yaml", ""))
    yaml = document.get("system_prompt", "")

    try:
        # Load crawler configuration
        crawler_config = CrawlerConfig.from_yaml(yaml, source_catalog_config=source_catalog_config)
        logger.info(f"Crawler configuration loaded successfully.")
        logger.debug(f"Crawler configuration: {crawler_config}")

        return crawler_config

    except Exception as e:
        logger.error(f"Error loading crawler configuration: {e}")


async def load_crawler_config_from_file(pipeline_config_yaml_file: str,
                                         source_catalog_config: List[SourceConfig] = None) -> CrawlerConfig:
    """Load pipeline configuration from a YAML file."""
    
    yaml_str = ''

    with open(pipeline_config_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load crawler configuration
        crawler_config = CrawlerConfig.from_yaml(yaml_str, source_catalog_config=source_catalog_config)
        logger.info(f"Crawler configuration loaded successfully.")
        logger.debug(f"Crawler configuration: {crawler_config}")

        return crawler_config

    except Exception as e:
        logger.error(f"Error loading crawler configuration: {e}")

async def load_crawler(crawler_config: CrawlerConfig, 
                        source_catalog_config: List[SourceConfig] = None) -> "Crawler":
    """Load crawler from configuration."""
    
    if not crawler_config:
        raise ValueError("Crawler configuration cannot be None or empty.")

    if not isinstance(crawler_config, CrawlerConfig):
        raise TypeError(f"Expected CrawlerConfig instance, got {type(crawler_config)}")

    # Create the crawler instance
    crawler = await Crawler.create(crawler_config=crawler_config,
                                     source_catalog_config=source_catalog_config
                                    )

    logger.info(f"Crawler '{crawler.name}' loaded successfully.")

    return crawler