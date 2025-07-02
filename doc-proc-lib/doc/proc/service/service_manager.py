import logging

from doc.proc.utils.import_module import import_module
from doc.proc.service.service_base import ServiceBase
from doc.proc.service.service_config import ServiceConfig

logger = logging.getLogger(__name__)


async def get_service(service_config: ServiceConfig, instance_settings: dict = None) -> ServiceBase:
    """Get an instance of the specified service type."""

    # Validate service_config
    if not isinstance(service_config, ServiceConfig):
        raise TypeError(f"Service configuration must be an instance of ServiceConfig, got \"{type(service_config)}\"")
    
    if not service_config.name:
        raise ValueError("Service configuration must have a name.")
    
    if not service_config.type:
        raise ValueError("Service configuration must have a type.")

    logger.debug(f"Creating service instance name: {service_config.name} of type: {service_config.type}.")

    # Create service instance based on type
    if not service_config.module_name:
        raise ValueError("Service configuration must have a module name.")
    
    if not service_config.module_path:
        raise ValueError("Service configuration must have a module path.")
    
    if not service_config.class_name:
        raise ValueError("Service configuration must have a class name.")

    logger.debug(f"Service instance module name: {service_config.module_name}, module path: {service_config.module_path}, class name: {service_config.class_name}.")

    try:
        # Dynamically import the service class
        service_module = import_module(module_path=service_config.module_path, module_name=service_config.module_name)
        service_class = getattr(service_module, service_config.class_name)

        if not service_class:
            raise ValueError(f"Service class \"{service_config.class_name}\" not found in module \"{service_config.module_name}\" at path \"{service_config.module_path}\"")

        if not hasattr(service_class, '__call__'):
            raise TypeError(f"{service_config.class_name} is not callable or does not have a __call__ method.")

        # merge instance settings with service configuration settings
        # Extract setting names and default values from settings_schema
        settings = {}
        if service_config.settings_schema:
            for key, setting in service_config.settings_schema.dict().items():
                default = setting.default
                if default is not None:
                    settings[key] = default

        if instance_settings is not None:
            settings = {**settings, **instance_settings}
        
        logger.debug(f"Service instance settings: {settings}")

        # Create an instance of the service class
        service_instance = service_class(name=service_config.name, type=service_config.type, settings=settings)

        if not issubclass(service_class, ServiceBase):
            raise TypeError(f"Service class \"{service_config.class_name}\" must be a subclass of ServiceBase.")

        logger.debug(f"Service instance created successfully: {service_instance}")

        return service_instance
    
    except ImportError as e:
        logger.error(f"Failed to import service class \"{service_config.class_name}\" from module \"{service_config.module_name}\": {e}")
        raise ImportError(f"Failed to import service class \"{service_config.class_name}\" from module \"{service_config.module_name}\": {e}")
    except AttributeError as e:
        logger.error(f"Service class \"{service_config.class_name}\" not found in module \"{service_config.module_name}\": {e}")
        raise AttributeError(f"Service class \"{service_config.class_name}\" not found in module \"{service_config.module_name}\": {e}")
    except Exception as e:
        logger.error(f"Error creating service instance: {e}")
        raise RuntimeError(f"Error creating service instance: {e}")