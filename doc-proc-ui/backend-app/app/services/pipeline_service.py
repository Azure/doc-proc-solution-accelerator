from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import yaml
import os

from app.services.base import BaseService
from app.db.cosmos import CosmosDb


class PipelineService(BaseService):
    """Service for managing pipeline operations"""
    
    def __init__(self, db: CosmosDb, container_name: str = "pipelines"):
        super().__init__(db, container_name)
        self._pipeline_cache = None
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate pipeline item"""
        required_fields = ["id", "name", "steps", "execution_sequence"]
        return all(field in item for field in required_fields)
    
    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines from configuration"""
        if self._pipeline_cache is None:
            pipelines = await self.list_all()
            self._pipeline_cache = pipelines
        return self._pipeline_cache
    
    async def get_pipeline_by_id(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline definition from config by id"""
        pipelines = await self.list_pipelines()
        for pipeline in pipelines:
            if pipeline.get("id") == pipeline_id:
                return pipeline
        return None
        
    async def get_pipeline_by_name(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get pipeline definition from config by name"""
        pipelines = await self.list_pipelines()
        for pipeline in pipelines:
            if pipeline.get("name") == pipeline_name:
                return pipeline
        return None
    
    async def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pipeline instance based on configuration"""
        
        # Generate unique ID if not provided
        pipeline_id = pipeline_data.get("id") or f"{pipeline_data.get('name')}_{int(time.time())}"
        
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_data.get("name"),
            "description": pipeline_data.get("description", ""),
            "version": pipeline_data.get("version", ""),
            "steps": pipeline_data.get("steps", []),
            "execution_sequence": pipeline_data.get("execution_sequence", []),
            "settings": pipeline_data.get("settings", {})
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
