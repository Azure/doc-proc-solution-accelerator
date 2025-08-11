import logging

from doc.proc.utils.import_module import import_module
from doc.proc.source.source_base import SourceBase
from doc.proc.service.source_config import SourceConfig

logger = logging.getLogger(__name__)


async def get_source(source_config: SourceConfig, instance_settings: dict = None) -> SourceBase:
    """Get an instance of the specified source type."""

    # Validate source_config
    if not isinstance(source_config, SourceConfig):
        raise TypeError(f"Source configuration must be an instance of SourceConfig, got \"{type(source_config)}\"")

    if not source_config.name:
        raise ValueError("Source configuration must have a name.")

    if not source_config.type:
        raise ValueError("Source configuration must have a type.")

    logger.debug(f"Creating source instance name: {source_config.name} of type: {source_config.type}.")

    # Create source instance based on type
    if not source_config.module_name:
        raise ValueError("Source configuration must have a module name.")

    if not source_config.module_path:
        raise ValueError("Source configuration must have a module path.")

    if not source_config.class_name:
        raise ValueError("Source configuration must have a class name.")

    logger.debug(f"Source instance module name: {source_config.module_name}, module path: {source_config.module_path}, class name: {source_config.class_name}.")

    try:
        # Dynamically import the source class
        source_module = import_module(module_path=source_config.module_path, module_name=source_config.module_name)
        source_class = getattr(source_module, source_config.class_name)

        if not source_class:
            raise ValueError(f"Source class \"{source_config.class_name}\" not found in module \"{source_config.module_name}\" at path \"{source_config.module_path}\"")

        if not hasattr(source_class, '__call__'):
            raise TypeError(f"{source_config.class_name} is not callable or does not have a __call__ method.")

        # merge instance settings with source configuration settings
        # Extract setting names and default values from settings_schema
        settings = {}
        if source_config.settings_schema:
            for key, setting in source_config.settings_schema.dict().items():
                default = setting.default
                if default is not None:
                    settings[key] = default

        if instance_settings is not None:
            settings = {**settings, **instance_settings}

        logger.debug(f"Source instance settings: {settings}")

        # Create an instance of the source class
        source_instance = source_class(name=source_config.name, type=source_config.type, settings=settings)

        if not issubclass(source_class, SourceBase):
            raise TypeError(f"Source class \"{source_config.class_name}\" must be a subclass of SourceBase.")

        logger.debug(f"Source instance created successfully: {source_instance}")

        return source_instance

    except ImportError as e:
        logger.error(f"Failed to import source class \"{source_config.class_name}\" from module \"{source_config.module_name}\": {e}")
        raise ImportError(f"Failed to import source class \"{source_config.class_name}\" from module \"{source_config.module_name}\": {e}")
    except AttributeError as e:
        logger.error(f"Source class \"{source_config.class_name}\" not found in module \"{source_config.module_name}\": {e}")
        raise AttributeError(f"Source class \"{source_config.class_name}\" not found in module \"{source_config.module_name}\": {e}")
    except Exception as e:
        logger.error(f"Error creating source instance: {e}")
        raise RuntimeError(f"Error creating source instance: {e}")