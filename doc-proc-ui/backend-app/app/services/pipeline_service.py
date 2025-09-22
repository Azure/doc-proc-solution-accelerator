from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


from app.services.base import BaseService
from app.db.cosmos import CosmosDb


class PipelineService(BaseService):
    """Service for managing pipeline operations"""
    
    def __init__(self, db: CosmosDb, container_name: str = "pipelines"):
        super().__init__(db, container_name)
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate pipeline item"""
        required_fields = ["id", "name", "steps", "execution_sequence"]
        return all(field in item for field in required_fields)
    
    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines from configuration"""
        pipelines = await self.list_all()
        return pipelines
    
    async def get_pipeline_by_id(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline definition from config by id"""
        return self.get_by_id(pipeline_id)
        
        
    async def get_pipeline_by_name(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get pipeline definition from config by name"""
        pipelines = await self.list_pipelines()
        for pipeline in pipelines:
            if pipeline.get("name") == pipeline_name:
                return pipeline
        return None
    
    async def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pipeline instance based on configuration"""
        
        # check is a pipeline with the same name already exists
        existing = await self.get_pipeline_by_name(pipeline_data.get("name"))
        if existing:
            raise ValueError(f"A pipeline with the name '{pipeline_data.get('name')}' already exists.")
        
        # Generate unique ID if not provided
        pipeline_id = pipeline_data.get("id") or f"{pipeline_data.get('name')}_{uuid.uuid4().hex[:8]}"
        pipeline_id = pipeline_id.replace(" ", "_").lower()
        
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_data.get("name"),
            "description": pipeline_data.get("description", ""),
            "version": pipeline_data.get("version", ""),
            "steps": pipeline_data.get("steps", []),
            "execution_sequence": pipeline_data.get("execution_sequence", []),
            "settings": pipeline_data.get("settings", {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if await self.validate_item(pipeline):
            return await self.create(pipeline)
        else:
            raise ValueError("Invalid pipeline data")
    
    async def update_by_id(self, pipeline_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a pipeline instance by ID"""
        existing = await self.get_by_id(pipeline_id)
        if not existing:
            raise ValueError("Pipeline not found")
        
        # Update allowed fields
        allowed_updates = ["description", "settings", "steps", "execution_sequence", "version"]
        for key, value in update_data.items():
            if key in allowed_updates:
                if key == "settings" and isinstance(value, dict):
                    existing["settings"] = {**existing.get("settings", {}), **value}
                else:
                    existing[key] = value
        
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
                
        if await self.validate_item(existing):
            updated = await self.update(existing)
            # Invalidate cache
            self._pipeline_cache = None
            return updated
        else:
            raise ValueError("Invalid pipeline data")


    async def delete_pipeline_by_id(self, pipeline_id: str) -> bool:
        """Delete a pipeline instance by ID"""
        existing = await self.get_by_id(pipeline_id)
        if not existing:
            return False
        
        # check if pipeline is in use by any vault
        from app.dependencies import get_vault_service
        vault_service = get_vault_service()
        
        in_use_vaults = await vault_service.check_pipeline_in_use_by_vault(existing["name"])
        if in_use_vaults:
            raise ValueError(f"Pipeline is in use by vaults: {in_use_vaults}")

        return await self.delete(pipeline_id)
        
    
    async def check_step_instance_in_use(self, step_instance_id: str) -> List[str]:
        """Check if a step instance is used in any pipeline"""
        # query = "SELECT * FROM c WHERE c.name=@name"
        # params = [{"name": "@name", "value": name}]
        # items = await self.query(query, params)
        
        pipelines = await self.list_pipelines()
        in_use_pipelines = []
        for pipeline in pipelines:
            steps = pipeline.get("steps", [])
            if step_instance_id in steps:
                in_use_pipelines.append(pipeline.get("name"))
        
        return in_use_pipelines