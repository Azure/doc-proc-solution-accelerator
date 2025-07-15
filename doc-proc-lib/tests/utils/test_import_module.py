"""
Unit tests for the import_module utility functions.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from doc.proc.utils.import_module import import_module, instantiate_class


class TestImportModule:
    """Test cases for import_module function."""
    
    def test_import_module_success(self):
        """Test successful module import."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def test_function():
    return "Hello from test module"

TEST_VARIABLE = "test_value"
''')
            temp_file = f.name
        
        try:
            # Import the module
            module = import_module(temp_file, "test_module")
            
            # Test that the module was imported correctly
            assert hasattr(module, 'test_function')
            assert hasattr(module, 'TEST_VARIABLE')
            assert module.test_function() == "Hello from test module"
            assert module.TEST_VARIABLE == "test_value"
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_import_module_file_not_found(self):
        """Test import_module with non-existent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            import_module("/nonexistent/path/module.py", "nonexistent_module")
        
        assert "Module file not found" in str(exc_info.value)
        assert "/nonexistent/path/module.py" in str(exc_info.value)
    
    def test_import_module_invalid_syntax(self):
        """Test import_module with invalid Python syntax."""
        # Create a temporary Python file with invalid syntax
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def invalid_syntax(:\n    pass')  # Invalid syntax
            temp_file = f.name
        
        try:
            with pytest.raises(Exception):  # Could be SyntaxError or other exception
                import_module(temp_file, "invalid_module")
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    @patch('importlib.util.spec_from_file_location')
    def test_import_module_import_error(self, mock_spec_from_file):
        """Test import_module when ImportError occurs."""
        mock_spec_from_file.side_effect = ImportError("Mocked import error")
        
        with pytest.raises(ImportError) as exc_info:
            import_module("/test/path.py", "test_module")
        
        assert "Could not import module 'test_module'" in str(exc_info.value)
        assert "Mocked import error" in str(exc_info.value)


class TestInstantiateClass:
    """Test cases for instantiate_class function."""
    
    def test_instantiate_class_success(self):
        """Test successful class instantiation."""
        # Create a temporary Python file with a class
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
class TestClass:
    def __init__(self):
        self.value = "test_instance"
    
    def get_value(self):
        return self.value
''')
            temp_file = f.name
        
        try:
            # Instantiate the class
            instance = instantiate_class(temp_file, "test_module", "TestClass")
            
            # Test that the instance was created correctly
            assert instance.value == "test_instance"
            assert instance.get_value() == "test_instance"
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_instantiate_class_class_not_found(self):
        """Test instantiate_class with non-existent class."""
        # Create a temporary Python file without the requested class
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
class ExistingClass:
    pass
''')
            temp_file = f.name
        
        try:
            with pytest.raises(AttributeError):
                instantiate_class(temp_file, "test_module", "NonExistentClass")
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_instantiate_class_not_callable(self):
        """Test instantiate_class with non-callable attribute."""
        # Create a temporary Python file with a non-callable attribute
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
NOT_A_CLASS = "just_a_string"
''')
            temp_file = f.name
        
        try:
            with pytest.raises(TypeError) as exc_info:
                instantiate_class(temp_file, "test_module", "NOT_A_CLASS")
            
            assert "is not callable" in str(exc_info.value)
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_instantiate_class_file_not_found(self):
        """Test instantiate_class with non-existent file."""
        with pytest.raises(Exception):  # Could be FileNotFoundError or other
            instantiate_class("/nonexistent/path/module.py", "test_module", "TestClass")
    
    def test_instantiate_class_with_constructor_params(self):
        """Test instantiate_class with a class that has constructor parameters."""
        # Create a temporary Python file with a class that takes parameters
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
class ParameterizedClass:
    def __init__(self, value="default"):
        self.value = value
    
    def get_value(self):
        return self.value
''')
            temp_file = f.name
        
        try:
            # Note: The current implementation calls the class with no parameters
            # So this will use the default parameter value
            instance = instantiate_class(temp_file, "test_module", "ParameterizedClass")
            
            assert instance.value == "default"
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_instantiate_class_inheritance(self):
        """Test instantiate_class with a class that inherits from another."""
        # Create a temporary Python file with inheritance
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
class BaseClass:
    def __init__(self):
        self.base_value = "base"
    
    def base_method(self):
        return "base_method"

class DerivedClass(BaseClass):
    def __init__(self):
        super().__init__()
        self.derived_value = "derived"
    
    def derived_method(self):
        return "derived_method"
''')
            temp_file = f.name
        
        try:
            instance = instantiate_class(temp_file, "test_module", "DerivedClass")
            
            # Test that both base and derived attributes/methods are available
            assert instance.base_value == "base"
            assert instance.derived_value == "derived"
            assert instance.base_method() == "base_method"
            assert instance.derived_method() == "derived_method"
        
        finally:
            # Clean up
            os.unlink(temp_file)
