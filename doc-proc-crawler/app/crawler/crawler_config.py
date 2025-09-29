import yaml

from pydantic import BaseModel, ValidationError
from typing import List, Optional, Tuple

from doc.proc.source.source_base import SourceBase
from doc.proc.source.source_config import SourceConfig
from doc.proc.source.source_base import SourceInstanceConfig
from doc.proc.source.source_manager import get_source

class CrawlerSettingsConfig(BaseModel):
    """Settings for the crawler execution."""
    enabled: Optional[bool] = True # Whether the crawler is enabled
    retry_delay: Optional[int] = 5  # Delay in seconds between retries
    timeout: Optional[int] = 300  # Timeout for the entire crawler execution in seconds
    max_concurrent_runs: Optional[int] = 5  # Maximum number of concurrent runs for the crawler

class CrawlerConfig(BaseModel):
    """Configuration for a single crawler."""
    name: str
    pipeline_name: str
    vault_id: str
    description: Optional[str] = None
    version: Optional[str] = None
    schedule: Optional[str] = None
    crawl_schedule: Optional[str] = None
    recrawl: Optional[bool] = None
    purge_schedule: Optional[str] = None
    execution_sequence: List[str] = None  # Order of step instance names
    settings: CrawlerSettingsConfig = CrawlerSettingsConfig()
    source_instances: List[SourceInstanceConfig] = []  # List of source instances used in the crawler

    @staticmethod
    def from_dict(config: dict) -> "CrawlerConfig":
        return CrawlerConfig(**config)

    @staticmethod
    def from_file(file_path: str) -> List["CrawlerConfig"]:
        """Load steps and crawlers configuration from a YAML file."""
        if not file_path:
            raise ValueError("File path cannot be empty")
        try:
            with open(file_path, 'r') as file:
                yaml_str = file.read()
            return CrawlerConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise ValueError(f"Configuration file '{file_path}' not found.")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the crawler configuration from file: {str(e)}")

    @staticmethod
    def from_yaml(yaml_str: str, 
                  source_catalog_config: List[SourceConfig] = None) -> List["CrawlerConfig"]:
        """Load steps and crawlers configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)

            source_instances: List[SourceInstanceConfig] = []
            
            if config.get("source_instances"):
                source_instances = [SourceInstanceConfig(**s) for s in config.get("source_instances", [])]

                if source_catalog_config:
                    for source in source_instances:
                        s_found = next((s for s in source_catalog_config if s.id == source.source_catalog_id), None)
                        if not s_found:
                            raise ValueError(f"Source instance '{source.name}' references unknown source catalog id '{source.source_catalog_id}' that could not be found in source catalog configuration. Available sources: {[s.id for s in source_catalog_config]}")

            # Load and validate crawlers
            if not config.get("crawlers"):
                raise ValueError("No crawlers found in the configuration.")

            crawlers = [CrawlerConfig.from_dict(c) for c in config.get("crawlers", [])]

            for crawler in crawlers:
                if not crawler.name:
                    raise ValueError(f"Crawler '{crawler.name}' is missing required fields.")

                crawler.source_instances = source_instances  # Assign source instances to the crawler

            return crawlers

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except ValidationError as ve:
            raise ValueError(f"Validation error in crawler configuration: {ve}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the crawler configuration: {str(e)}")