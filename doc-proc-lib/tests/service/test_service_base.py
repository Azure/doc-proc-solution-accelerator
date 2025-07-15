"""
Unit tests for the ServiceBase class and related components.
"""

import pytest
from doc.proc.service.service_base import ServiceBase, ServiceExecutionError


class ConcreteService(ServiceBase):
    """Concrete implementation of ServiceBase for testing."""
    
    async def test_connection(self) -> bool:
        """Simple test connection implementation."""
        return True


class FailingService(ServiceBase):
    """Service implementation that fails connection test."""
    
    async def test_connection(self) -> bool:
        """Always fails connection test."""
        raise ServiceExecutionError("Connection failed")


class TestServiceBase:
    """Test cases for ServiceBase."""
    
    def test_service_base_initialization_success(self):
        """Test successful ServiceBase initialization."""
        service = ConcreteService(
            name="test_service",
            type="test_type",
            settings={"key": "value"}
        )
        
        assert service.name == "test_service"
        assert service.type == "test_type"
        assert service.settings == {"key": "value"}
        assert service.params == {}
    
    def test_service_base_initialization_with_params(self):
        """Test ServiceBase initialization with additional parameters."""
        service = ConcreteService(
            name="test_service",
            type="test_type",
            settings={"key": "value"},
            extra_param="extra_value"
        )
        
        assert service.params == {"extra_param": "extra_value"}
    
    def test_service_base_initialization_empty_name(self):
        """Test ServiceBase initialization with empty name."""
        with pytest.raises(ValueError) as exc_info:
            ConcreteService(
                name="",
                type="test_type",
                settings={}
            )
        
        assert "Service name cannot be empty" in str(exc_info.value)
    
    def test_service_base_initialization_none_name(self):
        """Test ServiceBase initialization with None name."""
        with pytest.raises(ValueError) as exc_info:
            ConcreteService(
                name=None,
                type="test_type",
                settings={}
            )
        
        assert "Service name cannot be empty" in str(exc_info.value)
    
    def test_service_base_initialization_empty_type(self):
        """Test ServiceBase initialization with empty type."""
        with pytest.raises(ValueError) as exc_info:
            ConcreteService(
                name="test_service",
                type="",
                settings={}
            )
        
        assert "Service type cannot be empty" in str(exc_info.value)
    
    def test_service_base_initialization_none_type(self):
        """Test ServiceBase initialization with None type."""
        with pytest.raises(ValueError) as exc_info:
            ConcreteService(
                name="test_service",
                type=None,
                settings={}
            )
        
        assert "Service type cannot be empty" in str(exc_info.value)
    
    def test_service_base_initialization_none_settings(self):
        """Test ServiceBase initialization with None settings."""
        service = ConcreteService(
            name="test_service",
            type="test_type",
            settings=None
        )
        
        assert service.settings == {}  # Should default to empty dict
    
    @pytest.mark.asyncio
    async def test_concrete_service_test_connection(self):
        """Test concrete service test_connection method."""
        service = ConcreteService(
            name="test_service",
            type="test_type",
            settings={}
        )
        
        result = await service.test_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_abstract_service_test_connection_not_implemented(self):
        """Test that ServiceBase.test_connection raises NotImplementedError."""
        service = ServiceBase(
            name="test_service",
            type="test_type",
            settings={}
        )
        
        with pytest.raises(NotImplementedError):
            await service.test_connection()
    
    @pytest.mark.asyncio
    async def test_failing_service_test_connection(self):
        """Test service that raises ServiceExecutionError."""
        service = FailingService(
            name="failing_service",
            type="test_type",
            settings={}
        )
        
        with pytest.raises(ServiceExecutionError) as exc_info:
            await service.test_connection()
        
        assert str(exc_info.value) == "Connection failed"


class TestServiceExecutionError:
    """Test cases for ServiceExecutionError."""
    
    def test_service_execution_error_creation(self):
        """Test creating a ServiceExecutionError."""
        error = ServiceExecutionError("Test service error")
        assert str(error) == "Test service error"
    
    def test_service_execution_error_inheritance(self):
        """Test that ServiceExecutionError inherits from Exception."""
        error = ServiceExecutionError("Test error")
        assert isinstance(error, Exception)
