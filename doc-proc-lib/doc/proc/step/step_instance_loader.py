import logging

from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepConfig, StepInstanceConfig
from doc.proc.utils.import_module import import_module

logger = logging.getLogger("doc.proc.service.step_instance_loader")


def create_step_instance(step_config: StepConfig, step_instance_config: StepInstanceConfig) -> StepBase:
    """Get an instance of the specified step type."""

    # Validate the step configuration
    if not step_config.id:
        raise ValueError("Step configuration must have an id defined")

    module_name = step_config.module_name
    if not module_name:
        raise ValueError(f"Step \"{step_config.id}\" does not have a module defined")

    module_path = step_config.module_path
    if not module_path:
        raise ValueError(f"Step \"{step_config.id}\" does not have a module path defined")

    class_name = step_config.class_name
    if not class_name:
        raise ValueError(f"Step \"{step_config.id}\" does not have a class defined")

    # Import the module dynamically
    logger.debug(f"Importing step module: \"{module_name}\" from path: \"{module_path}\"")

    try:
        step_module = import_module(module_path=module_path, module_name=module_name)
        step_class = getattr(step_module, class_name, None)
        if not step_class:
            raise ValueError(f"Step \"{step_config.id}\" class \"{class_name}\" not found in module \"{module_name}\" at path \"{module_path}\"")

        if not hasattr(step_class, '__call__'):
            raise TypeError(f"{class_name} is not callable or does not have a __call__ method.")


        # Create an instance of the step class with the provided configuration
        step_instance = step_class(instance_config=step_instance_config) 

        if not isinstance(step_instance, StepBase):
            raise TypeError(f"Step \"{step_config.id}\" is not an instance of StepBase")

        return step_instance
    
    except ImportError as e:
        logger.error(f"Failed to import step class \"{step_config.class_name}\" from module \"{step_config.module_name}\". {e}")
        raise ImportError(f"Failed to import step class \"{step_config.class_name}\" from module \"{step_config.module_name}\". {e}")
    except AttributeError as e:
        logger.error(f"Step class \"{step_config.class_name}\" not found in module \"{step_config.module_name}\". {e}")
        raise AttributeError(f"Step class \"{step_config.class_name}\" not found in module \"{step_config.module_name}\". {e}")
    except Exception as e:
        logger.error(f"Error creating step instance: {e}")
        raise RuntimeError(f"Error creating step instance: {e}")