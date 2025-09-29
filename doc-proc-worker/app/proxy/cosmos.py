from typing import Any, Dict, Iterable, List, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions

from doc.proc.utils.azure import get_azure_credential


class CosmosDb():
    def __init__(self, 
                 endpoint: str, 
                 database_name: str, 
                 init_containers: Optional[List[str]] = None):
        super().__init__()
        
        if not endpoint:
            raise RuntimeError("Cosmos DB endpoint is required")

        self.client = CosmosClient(endpoint, credential=get_azure_credential())

        self.database = self._ensure_database(database_name)

        self.containers = {
            container: self._ensure_container(container) for container in (init_containers or [])
        }

    def _ensure_database(self, db_name: str):
        try:
            return self.client.create_database_if_not_exists(id=db_name)
        except exceptions.CosmosResourceExistsError:
            return self.client.get_database_client(db_name)

    def _ensure_container(self, container_name: str):
        try:
            return self.database.create_container_if_not_exists(id=container_name, partition_key=PartitionKey(path="/id"))
        except exceptions.CosmosResourceExistsError:
            return self.database.get_container_client(container_name)

    def upsert(self, container: str, item: Dict[str, Any]) -> Dict[str, Any]:
        return self.containers[container].upsert_item(item)

    def get(self, container: str, id: str) -> Optional[Dict[str, Any]]:
        try:
            return self.containers[container].read_item(item=id, partition_key=id)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def delete(self, container: str, item_id: str) -> bool:
        """Delete an item by ID"""
        try:
            self.containers[container].delete_item(item=item_id, partition_key=item_id)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
    
    def list(self, container: str, query: Optional[str] = None, parameters: Optional[Iterable[Dict[str, Any]]] = None):
        _container_proxy = self.containers.get(container)
        if not _container_proxy:
            _container_proxy = self._ensure_container(container)
            self.containers[container] = _container_proxy
        
        if query:
            return list(_container_proxy.query_items(query=query, parameters=parameters or [], enable_cross_partition_query=True))
        return list(_container_proxy.read_all_items())
