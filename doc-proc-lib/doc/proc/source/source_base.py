import logging
import hashlib

from typing import Dict, Any
from abc import abstractmethod
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from doc.proc.service.source_config import SourceConfig

logger = logging.getLogger(__name__)

class SourceExecutionError(Exception):
    """Custom exception for errors during source execution."""
    pass


class SourceConfigError(Exception):
    """Custom exception for errors in source configuration."""
    pass


class SourceBase:
    """Base class for data sources in the pipeline."""
    def __init__(self, name, type, settings: dict):
        self.name = name
        self.type = type
        self.settings = settings

    async def load_data(self) -> StepInputOutput:
        """Load data from the source."""
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