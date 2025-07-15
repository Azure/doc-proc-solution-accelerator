"""
Unit tests for the SampleService class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from doc.proc.service.sample_service import SampleService
from doc.proc.service.service_base import ServiceExecutionError


class TestSampleService:
    """Test cases for SampleService."""
    
    def test_sample_service_initialization_success(self, sample_service_settings):
        """Test successful SampleService initialization."""
        service = SampleService(
            name="test_sample_service",
            type="sample",
            settings=sample_service_settings
        )
        
        assert service.name == "test_sample_service"
        assert service.type == "sample"
        assert service.sample_setting == "required_value"
        assert service.sample_optional == 20
        assert service.sample_with_pattern == "valid_pattern"
        assert service.sample_enum == "option2"
        assert service.sample_sensitive == "secret_value"
        assert service.sample_boolean is True
    
    def test_sample_service_initialization_with_defaults(self):
        """Test SampleService initialization with default values."""
        minimal_settings = {
            "sample_setting": "required_value"
        }
        
        service = SampleService(
            name="test_service",
            type="sample",
            settings=minimal_settings
        )
        
        assert service.sample_setting == "required_value"
        assert service.sample_optional == 10  # Default value
        assert service.sample_enum == "option1"  # Default value
        assert service.sample_boolean is False  # Default value
    
    def test_sample_service_initialization_missing_required_setting(self):
        """Test SampleService initialization with missing required setting."""
        invalid_settings = {
            "sample_optional": 15
            # Missing sample_setting
        }
        
        with pytest.raises(ValueError) as exc_info:
            SampleService(
                name="test_service",
                type="sample",
                settings=invalid_settings
            )
        
        assert "Settings key 'sample_setting' is required" in str(exc_info.value)
    
    def test_sample_service_initialization_empty_required_setting(self):
        """Test SampleService initialization with empty required setting."""
        invalid_settings = {
            "sample_setting": ""  # Empty string
        }
        
        with pytest.raises(ValueError) as exc_info:
            SampleService(
                name="test_service",
                type="sample",
                settings=invalid_settings
            )
        
        assert "Settings key 'sample_setting' is required" in str(exc_info.value)
    
    def test_sample_service_initialization_none_required_setting(self):
        """Test SampleService initialization with None required setting."""
        invalid_settings = {
            "sample_setting": None
        }
        
        with pytest.raises(ValueError) as exc_info:
            SampleService(
                name="test_service",
                type="sample",
                settings=invalid_settings
            )
        
        assert "Settings key 'sample_setting' is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sample_service_test_connection_success(self, sample_service_settings):
        """Test successful connection test."""
        service = SampleService(
            name="test_service",
            type="sample",
            settings=sample_service_settings
        )
        
        result = await service.test_connection()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_sample_service_test_connection_minimal_settings(self):
        """Test connection test with minimal settings."""
        minimal_settings = {
            "sample_setting": "required_value"
        }
        
        service = SampleService(
            name="test_service",
            type="sample",
            settings=minimal_settings
        )
        
        result = await service.test_connection()
        assert result is True
    
    def test_sample_service_settings_extraction(self):
        """Test that settings are properly extracted and stored."""
        settings = {
            "sample_setting": "test_value",
            "sample_optional": 25,
            "sample_with_pattern": "pattern_value",
            "sample_enum": "option3",
            "sample_sensitive": "sensitive_data",
            "sample_boolean": True,
            "extra_setting": "ignored"  # This should be ignored
        }
        
        service = SampleService(
            name="test_service",
            type="sample",
            settings=settings
        )
        
        assert service.sample_setting == "test_value"
        assert service.sample_optional == 25
        assert service.sample_with_pattern == "pattern_value"
        assert service.sample_enum == "option3"
        assert service.sample_sensitive == "sensitive_data"
        assert service.sample_boolean is True
        
        # Extra setting should still be in the base settings dict
        assert service.settings["extra_setting"] == "ignored"
    
    def test_sample_service_inheritance(self, sample_service_settings):
        """Test that SampleService properly inherits from ServiceBase."""
        service = SampleService(
            name="test_service",
            type="sample",
            settings=sample_service_settings
        )
        
        # Should have inherited attributes from ServiceBase
        assert hasattr(service, 'name')
        assert hasattr(service, 'type')
        assert hasattr(service, 'settings')
        assert hasattr(service, 'params')
        
        # Should have the test_connection method
        assert hasattr(service, 'test_connection')
        assert callable(service.test_connection)
