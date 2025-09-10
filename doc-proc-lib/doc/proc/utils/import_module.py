import importlib
import importlib.util
import sys


def instantiate_class(module_path, module_name, class_name):    
    """
    Dynamically imports a Python module from the given file path and instantiates a class from it.

    Args:
        module_path (str): The file path to the module.
        class_name (str): The name of the class to instantiate.

    Returns:
        object: An instance of the specified class.
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    step_class = getattr(module, class_name)
    
    if not hasattr(step_class, '__call__'):
        raise TypeError(f"{class_name} is not callable or does not have a __call__ method.")
    
    return step_class()


def import_module(module_path, module_name):
    """
    Dynamically imports a Python module from the given file path and module name.

    Args:
        module_path (str): The file path to the module.
        module_name (str): The name to assign to the imported module.

    Returns:
        module: The imported module object.
    """

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}' from path '{module_path}': {str(e)}")
    except FileNotFoundError as e:
        # if the file is not found, this could be loaded from other workers.
        # use a different approach to load the module.
        module = f"{module_path.replace('/', '.').replace('.py', '').strip('..')}"
        loaded_module = importlib.import_module(module, "doc-proc-lib")
        return loaded_module
    except Exception as e:
        raise Exception(f"An error occurred while importing module '{module_name}': {str(e)}")
    finally:
        if module_name in sys.modules:
            del sys.modules[module_name]