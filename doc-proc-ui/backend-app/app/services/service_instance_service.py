from typing import Any, Dict, List, Optional
import yaml
import os
import time
import asyncio
from datetime import datetime, timezone
import logging

from app.services.base import BaseService
from app.services.service_catalog_service import ServiceCatalogService
from app.services.connection_tester import service_connection_tester
from app.db.cosmos import CosmosDb

logger = logging.getLogger("doc-proc-ui.app.services.service_instance")

class ServiceInstanceService(BaseService):
    """Service for managing service instance operations"""

    def __init__(self, db: CosmosDb, 
                       container_name: str = "service_instances",
                       catalog_service: ServiceCatalogService = None):
        
        super().__init__(db, container_name)
        
        self._catalog_service = catalog_service

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate service item against catalog schema"""
        required_fields = ["id", "name", "type"]
        return all(field in item for field in required_fields)
    
    
    async def create_service_instance(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a service instance based on catalog definition"""
        
        # get the catalog definition
        service_catalog_id = service_data.get("service_catalog_id")
        if not service_catalog_id:
            raise ValueError("service_catalog_id is required to create a service instance")

        catalog_service = await self._catalog_service.get_catalog_service_by_id(service_catalog_id)
        if not catalog_service:
            raise ValueError(f"Service catalog ID {service_catalog_id} not found")

        # Generate unique ID if not provided
        instance_id = service_data.get("id") or f"{service_data.get('name')}_{int(time.time())}"
        
        # Merge catalog definition with instance settings
        instance = {
            "id": instance_id,
            "name": service_data.get("name"),
            "description": service_data.get("description") or catalog_service.get("description"),
            "service_catalog_id": service_data.get("service_catalog_id"),
            "type": catalog_service.get("type"),
            "category": catalog_service.get("category"),
            "version": catalog_service.get("version"),
            "tags": catalog_service.get("tags", []),
            "settings": service_data.get("settings", {}),
            "catalog_definition": catalog_service,
            "status": "unknown",
            "connection_status": {
                "status": "unknown",
                "last_tested": None,
                "error_message": None,
                "test_duration_ms": None
            },
            "created_at": service_data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if await self.validate_item(instance):
            return await self.create(instance)
        else:
            raise ValueError("Invalid service instance data")
    
    async def update_service_instance(self, service_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing service instance"""
        existing = await self.get_by_id(service_id)
        if not existing:
            raise ValueError(f"Service instance {service_id} not found")
        
        # Update allowed fields
        allowed_updates = ["description", "settings", "status"]
        for key, value in updates.items():
            if key in allowed_updates:
                if key == "settings" and isinstance(value, dict):
                    existing["settings"] = {**existing.get("settings", {}), **value}
                else:
                    existing[key] = value
        
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return await self.update(existing)
    
    async def test_service_connection(self, service_id: str) -> Dict[str, Any]:
        """Test connection for a service instance"""
        service_instance = await self.get_by_id(service_id)
        if not service_instance:
            raise ValueError(f"Service instance {service_id} not found")
        
        # Update status to testing
        await self._update_connection_status(service_id, "testing")
        
        start_time = time.time()
        
        try:
            # Simulate connection test (in real implementation, you'd test the actual service)
            # For now, we'll simulate based on service type
            result = await self._perform_connection_test(service_instance)
            if not result:
                raise RuntimeError("Connection test failed. Received false result.")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            result = {
                "success": True,
                "status": "connected",
                "message": "Connection successful",
                "duration_ms": duration_ms,
                "tested_at": datetime.now(timezone.utc)
            }
            
            await self._update_connection_status(service_id, "connected", 
                                                 duration_ms=duration_ms)
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            result = {
                "success": False,
                "status": "error",
                "message": str(e),
                "duration_ms": duration_ms,
                "tested_at": datetime.now(timezone.utc)
            }
            
            await self._update_connection_status(service_id, "error", 
                                                 error_message=str(e),
                                                 duration_ms=duration_ms)
        
        return result
    
    async def _perform_connection_test(self, service_instance: Dict[str, Any]) -> bool:
        """Perform actual connection test based on service type"""
        try:
            test_result = await service_connection_tester.test_connection(service_instance)
            return test_result
        except Exception as e:
            raise e
    
    async def _update_connection_status(self, service_id: str, status: str, 
                                      error_message: Optional[str] = None,
                                      duration_ms: Optional[int] = None):
        """Update connection status for a service"""
        service_instance = await self.get_by_id(service_id)
        if service_instance:
            connection_status = {
                "status": status,
                "last_tested": datetime.now(timezone.utc).isoformat(),
                "error_message": error_message,
                "test_duration_ms": duration_ms
            }
            service_instance["connection_status"] = connection_status
            service_instance["status"] = status
            service_instance["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.update(service_instance)
    
    