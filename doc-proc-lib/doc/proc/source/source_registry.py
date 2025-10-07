import logging
from typing import Dict, List, Optional
import yaml

from doc.proc.source.source_config import SourceConfig
from doc.proc.source.source_instance_loader import create_source_instance
from doc.proc.source.source_base import SourceBase

logger = logging.getLogger("doc.proc.source.source_registry")


class SourceRegistry:
    """Registry for managing available data sources."""
    
    def __init__(self):
        self._sources: Dict[str, SourceConfig] = {}
        self._instances: Dict[str, SourceBase] = {}

    def load_from_yaml(self, file_path: str) -> None:
        """Load source configurations from a YAML file."""
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            
            for source_data in data.get('sources', []):
                source_config = SourceConfig(**source_data)
                self._sources[source_config.id] = source_config
                logger.info(f"Loaded source configuration: {source_config.id}")
                
        except Exception as e:
            logger.error(f"Failed to load source configurations from {file_path}: {e}")
            raise

    def register_source(self, source_config: SourceConfig) -> None:
        """Register a single source configuration."""
        self._sources[source_config.id] = source_config
        logger.info(f"Registered source: {source_config.id}")

    def get_source_config(self, source_id: str) -> Optional[SourceConfig]:
        """Get source configuration by ID."""
        return self._sources.get(source_id)

    def list_sources(self) -> List[SourceConfig]:
        """List all registered source configurations."""
        return list(self._sources.values())

    def list_source_ids(self) -> List[str]:
        """List all registered source IDs."""
        return list(self._sources.keys())

    def create_source_instance(self, 
                              source_id: str, 
                              instance_name: str,
                              instance_settings: Dict = None) -> SourceBase:
        """
        Create a source instance from registered configuration.
        
        Args:
            source_id: ID of the registered source configuration
            instance_name: Name for the new instance
            instance_settings: Override settings for the instance
            
        Returns:
            SourceBase: Created source instance
        """
        source_config = self.get_source_config(source_id)
        if not source_config:
            raise ValueError(f"Source configuration not found: {source_id}")

        # Create a copy of the config with the instance name
        instance_config = SourceConfig(
            id=source_config.id,
            name=instance_name,
            description=source_config.description,
            type=source_config.type,
            module_name=source_config.module_name,
            module_path=source_config.module_path,
            class_name=source_config.class_name,
            settings_schema=source_config.settings_schema,
            ui_metadata=source_config.ui_metadata,
            tags=source_config.tags
        )

        instance = create_source_instance(instance_config, instance_settings)
        
        # Cache the instance
        cache_key = f"{source_id}_{instance_name}"
        self._instances[cache_key] = instance
        
        logger.info(f"Created source instance: {instance_name} (type: {source_config.type})")
        return instance

    def get_cached_instance(self, source_id: str, instance_name: str) -> Optional[SourceBase]:
        """Get a cached source instance."""
        cache_key = f"{source_id}_{instance_name}"
        return self._instances.get(cache_key)

    def remove_cached_instance(self, source_id: str, instance_name: str) -> None:
        """Remove a cached source instance."""
        cache_key = f"{source_id}_{instance_name}"
        if cache_key in self._instances:
            del self._instances[cache_key]

    def clear_cache(self) -> None:
        """Clear all cached instances."""
        self._instances.clear()

    def get_sources_by_type(self, source_type: str) -> List[SourceConfig]:
        """Get all sources of a specific type."""
        return [config for config in self._sources.values() if config.type == source_type]

    def get_sources_by_tag(self, tag: str) -> List[SourceConfig]:
        """Get all sources with a specific tag."""
        return [
            config for config in self._sources.values() 
            if config.tags and tag in config.tags
        ]

    def __len__(self) -> int:
        return len(self._sources)

    def __contains__(self, source_id: str) -> bool:
        return source_id in self._sources


# Global registry instance
source_registry = SourceRegistry()


def load_source_catalog(file_path: str = "source_catalog.yaml") -> None:
    """Load sources from the default catalog file."""
    source_registry.load_from_yaml(file_path)


def get_source_registry() -> SourceRegistry:
    """Get the global source registry."""
    return source_registry