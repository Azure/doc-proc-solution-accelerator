from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.db.cosmos import CosmosDb


class BaseService(ABC):
    """Base service class for common CRUD operations"""
    
    def __init__(self, db: CosmosDb, container_name: str):
        self.db = db
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
    
    async def query(self, query: str, parameters: Optional[List[Dict[str, Any]]] = None, container: Optional[str] = None) -> List[Dict[str, Any]]:
        """Execute a query"""
        target_container = container or self.container_name
        return self.db.list(target_container, query, parameters)
    
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
