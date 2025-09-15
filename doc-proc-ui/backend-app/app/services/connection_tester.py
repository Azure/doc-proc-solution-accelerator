"""
Service connection testing module.

This module provides functionality to test connections to various service types.
"""
import asyncio
import logging
from typing import Dict, Any

from app.services.service_instance_loader import create_service_instance

logger = logging.getLogger("doc-proc-ui.app.services.connection_tester")


class ServiceConnectionTester:
    """Base class for testing service connections"""
    
    def __init__(self):
        self.test_timeout = 30  # 30 seconds default timeout
    
    async def test_connection(self, service_instance: Dict[str, Any]) -> bool:
        """Test connection to a service instance"""
        service_type = service_instance.get("type", "")
        service_id = service_instance.get("id", "")
        
        logger.info(f"Testing connection for service {service_id} (type: {service_type})")
        
        try:
            test_method = self._run_test_connection
            result = await asyncio.wait_for(
                test_method(service_instance), 
                timeout=self.test_timeout
            )
            
            logger.info(f"Connection test successful for {service_id}")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Connection test timeout for {service_id}")
            raise Exception(f"Connection test timeout after {self.test_timeout}s")
        except Exception as e:
            logger.error(f"Connection test failed for {service_id}: {str(e)}")
            raise
    
    async def _run_test_connection(self, service_instance: Dict[str, Any]) -> bool:
        """Test Azure Blob Storage connection"""

        instance_settings = service_instance.get("settings", {})
        
        # create an instance if the service and run the test connection method.
        service_catalog_definition = service_instance.get("catalog_definition")
        if not service_catalog_definition:
            raise Exception("Service catalog definition not defined in settings")

        _instance = create_service_instance(service_catalog_definition, instance_settings)
        result = await _instance.test_connection()

        return result
    
    
# Global instance
service_connection_tester = ServiceConnectionTester()
