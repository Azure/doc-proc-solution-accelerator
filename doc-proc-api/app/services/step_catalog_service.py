from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import yaml
import os

from app.services.base import BaseService
from app.db.cosmos import CosmosDb

logger = logging.getLogger("doc-proc-ui.app.services.step_catalog")

class StepCatalogService(BaseService):
    """Service for managing step catalog operations"""
    
    def __init__(self, db: CosmosDb, container_name: str = "step_catalog"):
        super().__init__(db, container_name)
        self._step_catalog_cache = None
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate step item against catalog schema"""
        required_fields = ["id", "name", "type", "module_name", "class_name"]
        return all(field in item for field in required_fields)
    
    async def _load_catalog_from_yaml(self) -> Dict[str, Any]:
        """Load step catalog from YAML file"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/step_catalog.yaml")
        catalog = {"step_catalog": []}
        
        try:
            with open(catalog_path, 'r') as file:
                catalog = yaml.safe_load(file)
        except FileNotFoundError as e:
            logger.error(f"Error loading step catalog from path {catalog_path}: {e}")
            raise e
        
        return catalog
    
    async def initialize_step_catalog(self) -> Dict[str, Any]:
        """Initialize step definitions from catalog if they don't exist"""
        logger.info("Initializing step definitions from catalog...")
        
        _catalog = await self._load_catalog_from_yaml()
        steps = _catalog.get("step_catalog", [])
        
            
        # Store catalog steps in Cosmos DB for persistence and updates
        result = await self._sync_catalog_steps_to_db(steps)

        logger.info(f"Added {result.get('created_count', 0)} new steps from catalog to database")
        
        # run again to get updated count
        catalog_steps = await self.list_catalog_steps()
        self._step_catalog_cache = catalog_steps
        logger.info(f"Total steps in catalog: {len(catalog_steps)}")
        
        return {
            "created_count": result.get("created_count", 0),
            "total_catalog_steps": len(catalog_steps)
        }
    
    async def _sync_catalog_steps_to_db(self, catalog_steps: List[Dict[str, Any]]):
        """Sync catalog steps to Cosmos DB catalog container"""
        
        created_count = 0
        
        for step in catalog_steps:
            step_id = step.get("id")
            existing = await self.get_by_id(step_id)
                        
            # Only update if not exists or version changed
            if not existing or existing.get("version") != step.get("version"):
                step_doc = {
                    **step,
                    "catalog_type": "step_definition",
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
                await self.update(step_doc)
                created_count += 1

        return {"created_count": created_count}
    
    async def list_catalog_steps(self) -> List[Dict[str, Any]]:
        """List all steps from catalog"""
        if self._step_catalog_cache is None:
            steps = await self.list_all()
            self._step_catalog_cache = steps
        return self._step_catalog_cache
    
    async def get_catalog_step_by_id(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get step definition from catalog by ID"""
        catalog_steps = await self.list_catalog_steps()
        for step in catalog_steps:
            if step.get("id") == step_id:
                return step
        return None