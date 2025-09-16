from typing import Any, Dict, List, Optional
import yaml
import os
import time
from datetime import datetime, timezone
import logging

from app.services.base import BaseService
from app.services.step_catalog_service import StepCatalogService
from app.db.cosmos import CosmosDb

logger = logging.getLogger("doc-proc-ui.app.services.step_instance")

class StepInstanceService(BaseService):
    """Service for managing service instance operations"""

    def __init__(self, db: CosmosDb, 
                       container_name: str = "step_instances",
                       catalog_service: StepCatalogService = None):
        
        super().__init__(db, container_name)
        
        self._catalog_service = catalog_service

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate step instance item against catalog schema"""
        required_fields = ["id", "name", "step_catalog_id", "enabled"]
        return all(field in item for field in required_fields)
    
    
    async def create_step_instance(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a step instance based on catalog definition"""
        
        # get the catalog definition
        step_catalog_id = step_data.get("step_catalog_id")
        if not step_catalog_id:
            raise ValueError("step_catalog_id is required to create a step instance")

        catalog_step = await self._catalog_service.get_catalog_step_by_id(step_catalog_id)
        if not catalog_step:
            raise ValueError(f"Step catalog ID {step_catalog_id} not found")

        # Generate unique ID if not provided
        instance_id = step_data.get("id") or f"{step_data.get('name')}_{int(time.time())}"
        instance_id = instance_id.replace(" ", "_").lower()
        
        # Merge catalog definition with instance settings
        instance = {
            "id": instance_id,
            "name": step_data.get("name"),
            "description": step_data.get("description") or catalog_step.get("description"),
            "step_catalog_id": step_catalog_id,
            "category": catalog_step.get("category"),
            "version": catalog_step.get("version"),
            "tags": catalog_step.get("tags", []),
            "settings": step_data.get("settings", {}),
            "enabled": step_data.get("enabled", True),
            "fail_pipeline_on_error": step_data.get("fail_pipeline_on_error", False),
            "timeout": step_data.get("timeout", 30),
            "services": step_data.get("services", []),
            "condition": step_data.get("condition", ""),
            "debug_mode": step_data.get("debug_mode", False),
            "catalog_definition": catalog_step,
            "created_at": step_data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
             
        if await self.validate_item(instance):
            return await self.create(instance)
        else:
            raise ValueError("Invalid service instance data")
    
    async def update_step_instance(self, step_instance_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing step instance"""
        existing = await self.get_by_id(step_instance_id)
        if not existing:
            raise ValueError(f"Step instance {step_instance_id} not found")
        
        # Update allowed fields
        allowed_updates = ["description", "settings", "enabled", "fail_pipeline_on_error", "timeout", "services", "condition", "debug_mode"]
        for key, value in updates.items():
            if key in allowed_updates:
                if key == "settings" and isinstance(value, dict):
                    existing["settings"] = {**existing.get("settings", {}), **value}
                else:
                    existing[key] = value
        
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return await self.update(existing)
    
    