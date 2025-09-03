from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.db.cosmos import CosmosDb
from app.services.azure_service import AzureService


class COSMOSDBService(AzureService, ABC):
    """Base service class for common COSMOS DB CRUD operations"""
    
    def __init__(self, container_name: str):
        self.db = CosmosDb(credential=self._get_credential())
        self.container_name = container_name
    
    async def create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        return self.db.upsert(self.container_name, item)
    
    async def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        return self.db.get(self.container_name, item_id)
    
    async def list_all(self, query: Optional[str] = None, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """List all items"""
        return self.db.list(self.container_name, query, parameters)
    
    async def update(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item"""
        return self.db.upsert(self.container_name, item)
    
    async def delete(self, item_id: str) -> bool:
        """Delete an item by ID"""
        try:
            self.db.containers[self.container_name].delete_item(item=item_id, partition_key=item_id)
            return True
        except Exception:
            return False
    
    @abstractmethod
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate item before creating/updating"""
        pass

