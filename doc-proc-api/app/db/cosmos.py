from typing import Any, Dict, Iterable, Optional
from functools import lru_cache

from azure.cosmos import CosmosClient, PartitionKey, exceptions

from app.utils import get_azure_credential

class CosmosDb:
    def __init__(self, 
                 endpoint: str, 
                 credential = None,
                 db_name: str = "docproc",
                 initial_containers: list[str] = []) -> None:
        if not endpoint:
            raise ValueError("Cosmos DB endpoint is required")
        
        if not db_name:
            raise ValueError("Cosmos DB name is required")

        if credential:
            self.client = CosmosClient(endpoint, credential=credential)
        else:
            self.client = CosmosClient(endpoint, credential=get_azure_credential())

        self.database = self._ensure_database(db_name)

        # Ensure initial containers are created in the database
        if initial_containers and len(initial_containers) > 0:
            self.containers = {
                container: self._ensure_container(container) for container in initial_containers
            }
        else:
            self.containers = {}

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
        if container not in self.containers:
            self.containers[container] = self._ensure_container(container)
            
        return self.containers[container].upsert_item(item)

    def get(self, container: str, id: str) -> Optional[Dict[str, Any]]:
        try:
            if container not in self.containers:
                self.containers[container] = self._ensure_container(container)
                
            return self.containers[container].read_item(item=id, partition_key=id)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def list(self, container: str, query: Optional[str] = None, parameters: Optional[Iterable[Dict[str, Any]]] = None):
        if container not in self.containers:
            self.containers[container] = self._ensure_container(container)

        if query:
            return list(self.containers[container].query_items(query=query, parameters=parameters or None, enable_cross_partition_query=True))

        return list(self.containers[container].read_all_items())
