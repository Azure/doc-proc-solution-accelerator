import logging

from doc.proc.utils.import_module import import_module
from doc.proc.service.service_base import ServiceBase

logger = logging.getLogger("doc-proc-ui.app.services.service_instance_loader")


def create_service_instance(service_catalog_definition: dict, instance_settings: dict) -> ServiceBase:
    """Get an instance of the specified service type."""

    # Validate service_catalog_definition
    if not isinstance(service_catalog_definition, dict):
        raise TypeError(f"Service catalog definition must be a dictionary, got \"{type(service_catalog_definition)}\"")

    if not service_catalog_definition.get("name"):
        raise ValueError("Service catalog definition must have a name.")

    if not service_catalog_definition.get("type"):
        raise ValueError("Service catalog definition must have a type.")

    logger.debug(f"Creating service instance name: {service_catalog_definition['name']} of type: {service_catalog_definition['type']}.")

    # Create service instance based on type
    if not service_catalog_definition.get("module_name"):
        raise ValueError("Service catalog definition must have a module name.")

    if not service_catalog_definition.get("module_path"):
        raise ValueError("Service catalog definition must have a module path.")

    if not service_catalog_definition.get("class_name"):
        raise ValueError("Service catalog definition must have a class name.")

    logger.debug(f"Service instance module name: {service_catalog_definition['module_name']}, module path: {service_catalog_definition['module_path']}, class name: {service_catalog_definition['class_name']}.")

    try:
        # Dynamically import the service class
        service_module = import_module(module_path=service_catalog_definition['module_path'], module_name=service_catalog_definition['module_name'])
        service_class = getattr(service_module, service_catalog_definition['class_name'])

        if not service_class:
            raise ValueError(f"Service class \"{service_catalog_definition['class_name']}\" not found in module \"{service_catalog_definition['module_name']}\" at path \"{service_catalog_definition['module_path']}\"")

        if not hasattr(service_class, '__call__'):
            raise TypeError(f"{service_catalog_definition['class_name']} is not callable or does not have a __call__ method.")

        # merge instance settings with service configuration settings
        # Extract setting names and default values from settings_schema
        settings = {}
        if service_catalog_definition.get("settings_schema"):
            for key, setting in service_catalog_definition['settings_schema'].items():
                default = setting.get("default", None)
                if default is not None:
                    settings[key] = default

        if instance_settings is not None:
            settings = {**settings, **instance_settings}
        
        logger.debug(f"Service instance settings: {settings}")

        # Create an instance of the service class
        service_instance = service_class(name=service_catalog_definition['name'], type=service_catalog_definition['type'], settings=settings)

        if not issubclass(service_class, ServiceBase):
            raise TypeError(f"Service class \"{service_catalog_definition['class_name']}\" must be a subclass of ServiceBase.")

        logger.debug(f"Service instance created successfully: {service_instance}")

        return service_instance
    
    except ImportError as e:
        logger.error(f"Failed to import service class \"{service_catalog_definition['class_name']}\" from module \"{service_catalog_definition['module_name']}\". {e}")
        raise ImportError(f"Failed to import service class \"{service_catalog_definition['class_name']}\" from module \"{service_catalog_definition['module_name']}\". {e}")
    except AttributeError as e:
        logger.error(f"Service class \"{service_catalog_definition['class_name']}\" not found in module \"{service_catalog_definition['module_name']}\". {e}")
        raise AttributeError(f"Service class \"{service_catalog_definition['class_name']}\" not found in module \"{service_catalog_definition['module_name']}\". {e}")
    except Exception as e:
        logger.error(f"Error creating service instance: {e}")
        raise RuntimeError(f"Error creating service instance: {e}")