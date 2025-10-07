import logging
from typing import Dict, List, Optional
import yaml

from doc.proc.step.step_config import StepConfig, StepInstanceConfig
from doc.proc.step.step_instance_loader import create_step_instance
from doc.proc.step.step_base import StepBase

logger = logging.getLogger("doc.proc.step.step_registry")


class StepRegistry:
    """Registry for managing available pipeline steps."""
    
    def __init__(self):
        self._steps: Dict[str, StepConfig] = {}
        self._instances: Dict[str, StepBase] = {}

    def load_from_yaml(self, file_path: str) -> None:
        """Load step configurations from a YAML file."""
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            
            step_configs = StepConfig.from_file(file_path)
            self._steps = {step_config.id: step_config for step_config in step_configs}

            logger.info(f"Loaded {len(self._steps.keys())} step configurations from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load step configurations from {file_path}: {e}")
            raise

    def register_step(self, step_config: StepConfig) -> None:
        """Register a single step configuration."""
        self._steps[step_config.id] = step_config
        logger.info(f"Registered step: {step_config.id}")

    def get_step_config(self, step_id: str) -> Optional[StepConfig]:
        """Get step configuration by ID."""
        return self._steps.get(step_id)

    def list_steps(self) -> List[StepConfig]:
        """List all registered step configurations."""
        return list(self._steps.values())

    def list_step_ids(self) -> List[str]:
        """List all registered step IDs."""
        return list(self._steps.keys())

    def create_step_instance(self, 
                           step_id: str, 
                           instance_config: StepInstanceConfig) -> StepBase:
        """
        Create a step instance from registered configuration.
        
        Args:
            step_id: ID of the registered step configuration
            instance_config: Configuration for the step instance
            
        Returns:
            StepBase: Created step instance
        """
        step_config = self.get_step_config(step_id)
        if not step_config:
            raise ValueError(f"Step configuration not found: {step_id}")

        instance = create_step_instance(step_config, instance_config)
        
        # Cache the instance
        cache_key = f"{step_id}_{instance_config.name}"
        self._instances[cache_key] = instance
        
        logger.info(f"Created step instance: {instance_config.name} (type: {step_config.class_name})")
        return instance

    def get_cached_instance(self, step_id: str, instance_name: str) -> Optional[StepBase]:
        """Get a cached step instance."""
        cache_key = f"{step_id}_{instance_name}"
        return self._instances.get(cache_key)

    def remove_cached_instance(self, step_id: str, instance_name: str) -> None:
        """Remove a cached step instance."""
        cache_key = f"{step_id}_{instance_name}"
        if cache_key in self._instances:
            del self._instances[cache_key]

    def clear_cache(self) -> None:
        """Clear all cached instances."""
        self._instances.clear()

    def get_steps_by_category(self, category: str) -> List[StepConfig]:
        """Get all steps of a specific category."""
        return [config for config in self._steps.values() if config.category == category]

    def get_steps_by_tag(self, tag: str) -> List[StepConfig]:
        """Get all steps with a specific tag."""
        return [
            config for config in self._steps.values() 
            if config.tags and tag in config.tags
        ]

    def __len__(self) -> int:
        return len(self._steps)

    def __contains__(self, step_id: str) -> bool:
        return step_id in self._steps


# Global registry instance
step_registry = StepRegistry()


def load_step_catalog(file_path: str = "step_catalog.yaml") -> None:
    """Load steps from the default catalog file."""
    step_registry.load_from_yaml(file_path)


def get_step_registry() -> StepRegistry:
    """Get the global step registry."""
    return step_registry