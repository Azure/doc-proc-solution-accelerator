import logging
from typing import Dict, List, Optional
import yaml

from doc.proc.service.service_config import ServiceConfig, ServiceInstanceConfig
from doc.proc.service.service_instance_loader import create_service_instance
from doc.proc.service.service_base import ServiceBase

logger = logging.getLogger("doc.proc.service.service_registry")


class ServiceRegistry:
    """Registry for managing available services."""
    
    def __init__(self):
        self._services: Dict[str, ServiceConfig] = {}
        self._instances: Dict[str, ServiceBase] = {}

    def load_from_yaml(self, file_path: str) -> None:
        """Load service configurations from a YAML file."""
        try:
            service_configs = ServiceConfig.from_file(file_path)
            self._services = {service_config.id: service_config for service_config in service_configs}
            logger.info(f"Loaded {len(self._services.keys())} service configurations from {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to load service configurations from {file_path}: {e}")
            raise

    def register_service(self, service_config: ServiceConfig) -> None:
        """Register a single service configuration."""
        self._services[service_config.id] = service_config
        logger.info(f"Registered service: {service_config.id}")

    def get_service_config(self, service_id: str) -> Optional[ServiceConfig]:
        """Get service configuration by ID."""
        return self._services.get(service_id)

    def list_services(self) -> List[ServiceConfig]:
        """List all registered service configurations."""
        return list(self._services.values())

    def list_service_ids(self) -> List[str]:
        """List all registered service IDs."""
        return list(self._services.keys())

    def create_service_instance(self, 
                              service_id: str, 
                              instance_name: str,
                              instance_settings: Dict = None) -> ServiceBase:
        """
        Create a service instance from registered configuration.
        
        Args:
            service_id: ID of the registered service configuration
            instance_name: Name for the new instance
            instance_settings: Override settings for the instance
            
        Returns:
            ServiceBase: Created service instance
        """
        service_config = self.get_service_config(service_id)
        if not service_config:
            raise ValueError(f"Service configuration not found: {service_id}")

        instance = create_service_instance(instance_name, service_config, instance_settings)
        
        # Cache the instance
        cache_key = f"{service_id}_{instance_name}"
        self._instances[cache_key] = instance
        
        logger.info(f"Created service instance: {instance_name} (type: {service_config.type})")
        return instance

    def get_cached_instance(self, service_id: str, instance_name: str) -> Optional[ServiceBase]:
        """Get a cached service instance."""
        cache_key = f"{service_id}_{instance_name}"
        return self._instances.get(cache_key)

    def remove_cached_instance(self, service_id: str, instance_name: str) -> None:
        """Remove a cached service instance."""
        cache_key = f"{service_id}_{instance_name}"
        if cache_key in self._instances:
            del self._instances[cache_key]

    def clear_cache(self) -> None:
        """Clear all cached instances."""
        self._instances.clear()

    def get_services_by_type(self, service_type: str) -> List[ServiceConfig]:
        """Get all services of a specific type."""
        return [config for config in self._services.values() if config.type == service_type]

    def get_services_by_category(self, category: str) -> List[ServiceConfig]:
        """Get all services of a specific category."""
        return [config for config in self._services.values() if config.category == category]

    def get_services_by_tag(self, tag: str) -> List[ServiceConfig]:
        """Get all services with a specific tag."""
        return [
            config for config in self._services.values() 
            if config.tags and tag in config.tags
        ]

    def __len__(self) -> int:
        return len(self._services)

    def __contains__(self, service_id: str) -> bool:
        return service_id in self._services


# Global registry instance
service_registry = ServiceRegistry()


def load_service_catalog(file_path: str = "service_catalog.yaml") -> None:
    """Load services from the default catalog file."""
    service_registry.load_from_yaml(file_path)


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry."""
    return service_registry