import logging

from .service_base import ServiceBase

logger = logging.getLogger(__name__)


class SampleService(ServiceBase):
    """Sample service for demonstration purposes."""

    def __init__(self, name: str, type: str, **settings):
        super().__init__(name=name, type=type, **settings)

        # Initialize service-specific settings
        self.sample_setting = settings.get('sample_setting') 
        self.sample_optional = settings.get('sample_optional', 10)
        self.sample_with_pattern = settings.get('sample_with_pattern')
        self.sample_enum = settings.get('sample_enum', 'option1')
        self.sample_sensitive = settings.get('sample_sensitive')
        self.sample_boolean = settings.get('sample_boolean', False)

        # Validate sample_setting
        if not self.sample_setting:
            raise ValueError("Settings key 'sample_setting' is required")
        
    async def test_connection(self) -> bool:
        """Test the connection of the service."""
        
        return True
