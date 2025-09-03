from typing import Any, Dict, List, Optional
import yaml
import os

from .base import BaseService
from ..db.cosmos import CosmosDb


class ServiceCatalogService(BaseService):
    """Service for managing service catalog operations"""
    
    def __init__(self, db: CosmosDb):
        super().__init__(db, "services")
        self._catalog_cache = None
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate service item against catalog schema"""
        required_fields = ["id", "name", "type", "settings_schema"]
        return all(field in item for field in required_fields)
    
    async def get_catalog(self) -> Dict[str, Any]:
        """Load service catalog from YAML file"""
        if self._catalog_cache is None:
            catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/service_catalog.yaml")
            try:
                with open(catalog_path, 'r') as file:
                    self._catalog_cache = yaml.safe_load(file)
            except FileNotFoundError:
                self._catalog_cache = {"services_catalog": []}
        return self._catalog_cache
    
    async def get_catalog_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service definition from catalog by ID"""
        catalog = await self.get_catalog()
        for service in catalog.get("services_catalog", []):
            if service.get("id") == service_id:
                return service
        return None
    
    async def list_catalog_services(self) -> List[Dict[str, Any]]:
        """List all services from catalog"""
        catalog = await self.get_catalog()
        return catalog.get("services_catalog", [])
    
    async def create_service_instance(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a service instance based on catalog definition"""
        catalog_service = await self.get_catalog_service_by_id(service_data.get("service_catalog_id"))
        if not catalog_service:
            raise ValueError(f"Service catalog ID {service_data.get('service_catalog_id')} not found")
        
        # Merge catalog definition with instance settings
        instance = {
            "id": service_data.get("name"),
            "name": service_data.get("name"),
            "service_catalog_id": service_data.get("service_catalog_id"),
            "type": catalog_service.get("type"),
            "description": catalog_service.get("description"),
            "settings": service_data.get("settings", {}),
            "catalog_definition": catalog_service,
            "created_at": service_data.get("created_at"),
            "updated_at": service_data.get("updated_at")
        }
        
        if await self.validate_item(instance):
            return await self.create(instance)
        else:
            raise ValueError("Invalid service instance data")
    
    async def get_services_by_type(self, service_type: str) -> List[Dict[str, Any]]:
        """Get all service instances of a specific type"""
        query = "SELECT * FROM c WHERE c.type = @type"
        parameters = [{"name": "@type", "value": service_type}]
        return await self.list_all(query, parameters)
