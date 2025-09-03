from typing import Any, Dict, Iterable, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions

from app.settings import app_settings


class CosmosDb():
    def __init__(self, credential = None) -> None:
        settings = app_settings

        if not settings.COSMOS_DB_ENDPOINT:
            raise RuntimeError("COSMOS_DB_ENDPOINT is required")

        self.client = CosmosClient(settings.COSMOS_DB_ENDPOINT, credential=credential)

        self.database = self._ensure_database(settings.COSMOS_DB_NAME)
        
        self.containers = {
            "services": self._ensure_container(settings.COSMOS_DB_CONTAINER_SERVICES),
            "steps": self._ensure_container(settings.COSMOS_DB_CONTAINER_STEPS),
            "pipelines": self._ensure_container(settings.COSMOS_DB_CONTAINER_PIPELINES),
            "batch_executions": self._ensure_container(settings.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS),
            "activities": self._ensure_container(settings.COSMOS_DB_CONTAINER_ACTIVITIES),
            "step_outputs": self._ensure_container(settings.COSMOS_DB_CONTAINER_STEP_OUTPUTS),
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
