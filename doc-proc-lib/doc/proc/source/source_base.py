import logging
import hashlib

from typing import Optional, List, Dict, Any, Iterator, Tuple
from abc import abstractmethod

from doc.proc.source.source_config import SourceConfig

from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SourceExecutionError(Exception):
    """Custom exception for errors during source execution."""
    pass

class SourceInstanceConfig(BaseModel):
    name: str  # Instance name in the crawler
    source_catalog_id: str  # Reference to source id in the source catalog
    enabled : Optional[bool] = True  # Whether the source instance is enabled
    settings: Optional[dict] = None  # Additional settings for the source instance


class SourceConfigError(Exception):
    """Custom exception for errors in source configuration."""
    pass


class SourceBase:
    """Base class for data sources in the pipeline."""
    def __init__(self, id, name, type, settings: dict):
        self.id = id
        self.name = name
        self.type = type
        self.settings = settings

        from dependencies import get_config
        self.config = get_config()

    def replace_config_value(self, value):
        if value.startswith('${') and value.endswith('}'):
            env_var_name = value[2:-1]
            value = self.config.get(env_var_name)
        return value

    async def load_data(self):
        """Load data from the source."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    async def check_changes(self, request: DocProcRequest, state: DocProcState):
        raise NotImplementedError("Subclasses must implement this method.")
    
    async def check_exists(self, content_identifier : ContentIdentifier):
        raise NotImplementedError("Subclasses must implement this method.")
    
    async def get_content(self, contentUri:str):
        """Get content from the source."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    async def get_content_metadata(self, contentUri:str):
        """Get content metadata from the source."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    async def get_content_security(self, contentUri:str):
        """Get content security information from the source."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    async def get_items(self) -> Iterator:
        """Get content security information from the source."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    @staticmethod
    async def create(source_config: SourceConfig = None) -> "SourceBase":
        """Factory method to create a SourceBase instance from configuration."""

        logger.info("Creating source instance from configuration")

        if not source_config:
            raise SourceConfigError("Source configuration cannot be None")

        source_instance = SourceBase(source_config=source_config)

        logger.debug(f"Source instance '{source_instance.name}' created successfully.")
        return source_instance
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the service connection.
        This method should be overridden by subclasses to implement specific service tests.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
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