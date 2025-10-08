# Import source base classes from doc-proc-lib
from doc.proc.source.source_base import SourceBase, SourceItem, SourceItemMetadata
from doc.proc.source.source_instance_loader import create_source_instance
from doc.proc.source.source_config import SourceConfig
from typing import Dict, Any, List, Optional
import logging


class SourceManager:
    """Manager for creating and handling source instances using doc-proc-lib"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"doc-proc-crawler.sources.SourceManager")
    
    def create_source_from_instance(self, source_instance: Dict[str, Any], catalog_definition: Dict[str, Any]) -> SourceBase:
        """
        Create a source instance from source instance configuration and catalog definition.
        
        Args:
            source_instance: Source instance configuration dict
            catalog_definition: Source catalog definition dict
            
        Returns:
            SourceBase: Instance of the appropriate source class
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Create SourceConfig from catalog definition
            source_config = SourceConfig(**catalog_definition)
                        
            # Create source instance using doc-proc-lib
            source = create_source_instance(
                instance_name=source_instance.get('name', 'default_instance'),
                source_config=source_config,
                instance_settings=source_instance.get('settings', {})
            )
            
            self.logger.debug(f"Created source instance: {source}")
            return source
            
        except Exception as e:
            self.logger.error(f"Error creating source instance: {e}")
            raise RuntimeError(f"Failed to create source instance: {e}")
    
    async def test_source_connection(self, source: SourceBase) -> bool:
        """
        Test connection to a source.
        
        Args:
            source: Source instance to test
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            return await source.test_connection()
        except Exception as e:
            self.logger.error(f"Connection test failed for source {source.name}: {e}")
            return False