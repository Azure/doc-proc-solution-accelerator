from typing import Any, Dict, List, Optional
import yaml
import os

from app.services.base import BaseService
from app.db.cosmos import CosmosDb


class StepCatalogService(BaseService):
    """Service for managing step catalog operations"""
    
    def __init__(self, db: CosmosDb):
        super().__init__(db, "steps")
        self._catalog_cache = None
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate step item against catalog schema"""
        required_fields = ["id", "name", "type", "module_name", "class_name"]
        return all(field in item for field in required_fields)
    
    async def get_catalog(self) -> Dict[str, Any]:
        """Load step catalog from YAML file"""
        if self._catalog_cache is None:
            catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/step_catalog.yaml")
            try:
                with open(catalog_path, 'r') as file:
                    self._catalog_cache = yaml.safe_load(file)
            except FileNotFoundError:
                self._catalog_cache = {"step_catalog": []}
        return self._catalog_cache
    
    async def get_catalog_step_by_id(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get step definition from catalog by ID"""
        catalog = await self.get_catalog()
        for step in catalog.get("step_catalog", []):
            if step.get("id") == step_id:
                return step
        return None
    
    async def list_catalog_steps(self) -> List[Dict[str, Any]]:
        """List all steps from catalog"""
        catalog = await self.get_catalog()
        return catalog.get("step_catalog", [])
    
    async def create_step_instance(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a step instance based on catalog definition"""
        catalog_step = await self.get_catalog_step_by_id(step_data.get("step_catalog_id"))
        if not catalog_step:
            raise ValueError(f"Step catalog ID {step_data.get('step_catalog_id')} not found")
        
        # Merge catalog definition with instance settings
        instance = {
            "id": step_data.get("name"),
            "name": step_data.get("name"),
            "step_catalog_id": step_data.get("step_catalog_id"),
            "type": catalog_step.get("type"),
            "description": catalog_step.get("description"),
            "module_name": catalog_step.get("module_name"),
            "module_path": catalog_step.get("module_path"),
            "class_name": catalog_step.get("class_name"),
            "enabled": step_data.get("enabled", True),
            "fail_pipeline_on_error": step_data.get("fail_pipeline_on_error", False),
            "retry_on_failure": step_data.get("retry_on_failure", False),
            "retries": step_data.get("retries", 3),
            "timeout": step_data.get("timeout", 600),
            "services": step_data.get("services", []),
            "condition": step_data.get("condition"),
            "fail_step_on_document_error": step_data.get("fail_step_on_document_error", False),
            "debug_mode": step_data.get("debug_mode", False),
            "settings": step_data.get("settings", {}),
            "catalog_definition": catalog_step,
            "created_at": step_data.get("created_at"),
            "updated_at": step_data.get("updated_at")
        }
        
        if await self.validate_item(instance):
            return await self.create(instance)
        else:
            raise ValueError("Invalid step instance data")
    
    async def get_steps_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all step instances of a specific category"""
        catalog = await self.get_catalog()
        steps = []
        for step in catalog.get("step_catalog", []):
            if step.get("category") == category:
                steps.append(step)
        return steps
    
    async def get_steps_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get all step instances that match any of the provided tags"""
        catalog = await self.get_catalog()
        steps = []
        for step in catalog.get("step_catalog", []):
            step_tags = step.get("tags", [])
            if any(tag in step_tags for tag in tags):
                steps.append(step)
        return steps
