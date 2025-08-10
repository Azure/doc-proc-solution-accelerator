from typing import Any, Dict, Iterable, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions

from ..config import get_settings


class CosmosDb:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.cosmos_endpoint or not settings.cosmos_key:
            raise RuntimeError("COSMOS_ENDPOINT and COSMOS_KEY are required")
        self.client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
        self.database = self._ensure_database(settings.cosmos_db_name)
        self.containers = {
            "services": self._ensure_container(settings.container_services),
            "steps": self._ensure_container(settings.container_steps),
            "pipelines": self._ensure_container(settings.container_pipelines),
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

    def list(self, container: str, query: Optional[str] = None, parameters: Optional[Iterable[Dict[str, Any]]] = None):
        if query:
            return list(self.containers[container].query_items(query=query, parameters=parameters or [], enable_cross_partition_query=True))
        return list(self.containers[container].read_all_items())
