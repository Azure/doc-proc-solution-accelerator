from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging
import time

from app.services.base import BaseService
from app.services.source_catalog_service import SourceCatalogService
from app.db.cosmos import CosmosDb
from app.models.source import SourceInstanceCrawlerSettings

logger = logging.getLogger("doc-proc-ui.app.services.source_instance")

class SourceInstanceService(BaseService):
    """Service for managing source instance operations"""

    def __init__(self, db: CosmosDb, 
                       container_name: str = "source_instances",
                       catalog_service: SourceCatalogService = None):
        
        super().__init__(db, container_name)
        self.catalog_service = catalog_service

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate source instance item"""
        required_fields = ["id", "name", "source_catalog_id"]
        return all(field in item for field in required_fields)

    async def get_all_non_system(self) -> List[Dict[str, Any]]:
        """Get all non-system source instances"""
        query = "SELECT * FROM c WHERE c.is_system = false"
        items = await self.list_all(query)
        return items

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a source instance by name"""
        query = "SELECT * FROM c WHERE c.name=@name"
        params = [{"name": "@name", "value": name}]
        items = await self.query(query, params)
        return items[0] if items else None
    
    async def create_source_instance(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new source instance"""
        logger.info(f"Creating source instance: {source_data.get('name', 'unknown')}")

        # check if source instance with same name exists
        existing = await self.get_by_name(source_data.get("name"))
        if existing:
            raise ValueError(f"Source instance with name '{source_data.get('name')}' already exists")

        # get the catalog definition
        source_catalog_id = source_data.get("source_catalog_id")
        if not source_catalog_id:
            raise ValueError("source_catalog_id is required to create a source instance")

        # Validate the source catalog exists
        if self.catalog_service:
            catalog_source = await self.catalog_service.get_by_id(source_catalog_id)
            if not catalog_source:
                raise ValueError(f"Source catalog '{source_catalog_id}' not found")

        instance_id = source_data.get("id") or f"{source_data.get('name').strip()}_{int(time.time())}"
        instance_id = instance_id.replace(" ", "_").lower()
        
        crawler_settings = SourceInstanceCrawlerSettings().model_dump()
        if "crawler_settings" in source_data:
            crawler_settings.update(source_data["crawler_settings"])
        
        # Merge catalog definition with instance settings
        instance = {
            "id": instance_id,
            "name": source_data.get("name").strip(),
            "description": source_data.get("description") or catalog_source.get("description"),
            "source_catalog_id": source_catalog_id,
            "settings": source_data.get("settings", {}),
            "crawler_settings": crawler_settings,
            "enabled": source_data.get("enabled", True),
            "test_connection": source_data.get("test_connection", True),
            "status": None,
            "catalog_definition": catalog_source,
            "is_system": source_data.get("is_system", False),
            "created_at": source_data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
             
        if await self.validate_item(instance):
            return await self.create(instance)
        else:
            raise ValueError("Invalid source instance data")
        

    async def update_source_instance(self, instance_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing source instance"""
        logger.info(f"Updating source instance: {instance_id}")
        
        # Get existing instance
        existing = await self.get_by_id(instance_id)
        if not existing:
            raise ValueError(f"Source instance '{instance_id}' not found")
        
        # Validate catalog if being changed
        if "source_catalog_id" in update_data and self.catalog_service:
            catalog_source = await self.catalog_service.get_by_id(update_data["source_catalog_id"])
            if not catalog_source:
                raise ValueError(f"Source catalog '{update_data['source_catalog_id']}' not found")
        
        # Update metadata
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        updated_instance = {**existing, **update_data}

        if await self.validate_item(updated_instance):
            return await self.update(updated_instance)
        else:
            raise ValueError("Invalid source instance data")

    async def delete_source_instance_by_id(self, instance_id: str) -> bool:
        """Delete a source instance by ID"""
        logger.info(f"Deleting source instance: {instance_id}")
        from app.dependencies import get_vault_service
        
        try:
            existing = await self.get_by_id(instance_id)
            if not existing:
                logger.warning(f"Source instance '{instance_id}' not found for deletion")
                return False
            
            # get if any vault is associated with this source instance
            associated_vaults = []

            vault_service = get_vault_service()

            if vault_service:
                associated_vaults = await vault_service.get_vaults_by_source_instance_name(existing.get("name"))
                if associated_vaults:
                    raise ValueError(f"Cannot delete source instance '{instance_id}' as it is associated with existing vault(s). Please reassign or delete the vault(s) first.")
            else:
                logger.warning("VaultService not provided, cannot proceed with deletion of source instance.")
                raise ValueError("VaultService not available to check for associated vaults.")
            
            result = await self.delete(instance_id)
            if result:
                logger.info(f"Successfully deleted source instance: {instance_id}")
            else:
                logger.warning(f"Source instance '{instance_id}' not found for deletion")
            return result
        except Exception as e:
            logger.error(f"Failed to delete source instance '{instance_id}': {e}")
            raise
        
    async def delete_source_instance_by_name(self, instance_name: str) -> bool:
        """Delete a source instance by ID"""
        logger.info(f"Deleting source instance: {instance_name}")
        from app.dependencies import get_vault_service
        
        try:
            existing = await self.get_by_name(instance_name)
            if not existing:
                logger.warning(f"Source instance '{instance_name}' not found for deletion")
                return False
            
            # get if any vault is associated with this source instance
            associated_vaults = []

            vault_service = get_vault_service()

            if vault_service:
                associated_vaults = await vault_service.get_vaults_by_source_instance_name(existing.get("name"))
                if associated_vaults:
                    raise ValueError(f"Cannot delete source instance '{instance_name}' as it is associated with existing vault(s). Please reassign or delete the vault(s) first.")
            else:
                logger.warning("VaultService not provided, cannot proceed with deletion of source instance.")
                raise ValueError("VaultService not available to check for associated vaults.")
            
            result = await self.delete(existing.get("id"))
            if result:
                logger.info(f"Successfully deleted source instance: {instance_name}")
            else:
                logger.warning(f"Source instance '{instance_name}' not found for deletion")
            return result
        except Exception as e:
            logger.error(f"Failed to delete source instance '{instance_name}': {e}")
            raise

    async def test_source_instance_connection(self, instance_id: str) -> Dict[str, Any]:
        """Test connection for a source instance"""
        logger.info(f"Testing connection for source instance: {instance_id}")
        
        try:
            # Get the source instance
            instance = await self.get_by_id(instance_id)
            if not instance:
                raise ValueError(f"Source instance '{instance_id}' not found")
            
            # Get the catalog source for connection testing logic
            catalog_source = None
            if self.catalog_service:
                catalog_source = await self.catalog_service.get_by_id(instance.get("source_catalog_id"))
            
            # For now, we'll return a mock response since the actual source connection testing
            # would require loading and instantiating the source class
            # This should be implemented when the source classes are available
            
            result = {
                "instance_id": instance_id,
                "instance_name": instance.get("name"),
                "source_type": catalog_source.get("type") if catalog_source else "unknown",
                "status": "testing",  # Would be "connected" or "error" in real implementation
                "message": "Connection test functionality not yet implemented",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "catalog_found": catalog_source is not None,
                    "settings_provided": bool(instance.get("settings"))
                }
            }
            
            logger.info(f"Connection test completed for source instance: {instance_id}")
            return result
            
        except Exception as e:
            error_result = {
                "instance_id": instance_id,
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "tested_at": datetime.now(timezone.utc).isoformat()
            }
            logger.error(f"Connection test failed for source instance '{instance_id}': {e}")
            return error_result

    async def get_source_instances_by_catalog_id(self, catalog_id: str) -> List[Dict[str, Any]]:
        """Get all source instances for a specific catalog source"""
        try:
            query = "SELECT * FROM c WHERE c.source_catalog_id = @catalog_id"
            parameters = [{"name": "@catalog_id", "value": catalog_id}]
            
            sources = await self.query(query, parameters)
            logger.info(f"Retrieved {len(sources)} source instances for catalog ID '{catalog_id}'")
            return sources
        except Exception as e:
            logger.error(f"Failed to get source instances by catalog ID '{catalog_id}': {e}")
            raise

    async def get_enabled_source_instances(self) -> List[Dict[str, Any]]:
        """Get all enabled source instances"""
        try:
            query = "SELECT * FROM c WHERE c.enabled = true"
            
            sources = await self.query(query)
            logger.info(f"Retrieved {len(sources)} enabled source instances")
            return sources
        except Exception as e:
            logger.error(f"Failed to get enabled source instances: {e}")
            raise