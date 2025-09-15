from typing import Any, Dict, List, Optional
import yaml
import os
import time
import asyncio
from datetime import datetime, timezone
import logging

from app.services.base import BaseService
from app.services.connection_tester import service_connection_tester
from app.db.cosmos import CosmosDb

logger = logging.getLogger("doc-proc-ui.app.services.service_catalog")

class ServiceCatalogService(BaseService):
    """Service for managing service catalog operations"""

    def __init__(self, db: CosmosDb, 
                       container_name: str = "service_catalog"):
        
        super().__init__(db, container_name)
        self._service_catalog_cache = None

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate service item against catalog schema"""
        required_fields = ["id", "name", "type"]
        return all(field in item for field in required_fields)
    
    async def _load_catalog_from_yaml(self) -> Dict[str, Any]:
        """Load service catalog from YAML file"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../../doc-proc-lib/service_catalog.yaml")
        catalog = {"services_catalog": []}
        
        try:
            with open(catalog_path, 'r') as file:
                catalog = yaml.safe_load(file)
        except FileNotFoundError as e:
            logger.error(f"Error loading service catalog from path {catalog_path}: {e}")
            raise e
        
        return catalog
        
    async def initialize_service_catalog(self) -> Dict[str, Any]:
        """Initialize services from catalog if they don't exist"""
        logger.info("Initializing services from catalog...")
        
        _catalog = await self._load_catalog_from_yaml()
        services = _catalog.get("services_catalog", [])
            
        # Store catalog services in Cosmos DB for persistence and updates
        result = await self._sync_catalog_services_to_db(services)

        logger.info(f"Added {result.get('created_count', 0)} new services from catalog to database")
        
        # run again to get updated count
        catalog_services = await self.list_catalog_services()
        self._service_catalog_cache = catalog_services
        logger.info(f"Total services in catalog: {len(catalog_services)}")
        
        return {
            "created_count": result.get("created_count", 0),
            "total_catalog_services": len(catalog_services)
        }

    async def _sync_catalog_services_to_db(self, catalog_services: List[Dict[str, Any]]):
        """Sync catalog services to Cosmos DB catalog container"""
        
        created_count = 0
        
        for service in catalog_services:
            service_id = service.get("id")
            existing = await self.get_by_id(service_id)
                        
            # Only update if not exists or version changed
            if not existing or existing.get("version") != service.get("version"):
                service_doc = {
                    **service,
                    "catalog_type": "service_definition",
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
                await self.update(service_doc)
                created_count += 1

        return {"created_count": created_count}
    
    async def list_catalog_services(self) -> List[Dict[str, Any]]:
        """List all services from cosmos services_catalog"""
        if self._service_catalog_cache is None:
            services = await self.list_all()
            self._service_catalog_cache = services
        return self._service_catalog_cache
    
    async def get_catalog_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service definition from catalog by ID"""
        catalog_services = await self.list_catalog_services()
        for service in catalog_services:
            if service.get("id") == service_id:
                return service
        return None