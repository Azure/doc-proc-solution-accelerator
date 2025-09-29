from functools import lru_cache

from app.proxy.cosmos import CosmosDb
from app.proxy.queue import StorageQueue
from app.managers.pipeline_manager import PipelineManager
from app.managers.execution_manager import ExecutionManager

from configuration import Configuration

__config: Configuration = None

def get_config(action: str = None) -> Configuration:
    global __config

    if action is not None and action=='refresh':
        __config = Configuration()
    else:
        __config = __config or Configuration()
    return __config

@lru_cache(maxsize=1)
def get_cosmos_db() -> CosmosDb:
    """Get a singleton instance of CosmosDb"""
    from app.settings import app_settings
    return CosmosDb(endpoint=app_settings.COSMOS_DB_ENDPOINT,
                    database_name=app_settings.COSMOS_DB_NAME,
                    init_containers=app_settings.get_cosmos_db_containers())

@lru_cache(maxsize=1)
def get_queue_proxy() -> StorageQueue:
    """Get StorageQueue instance"""
    from app.settings import app_settings
    return StorageQueue(storage_account_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                        queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME)

@lru_cache(maxsize=1)
def get_pipeline_manager() -> PipelineManager:
    """Get PipelineManager instance"""
    from app.settings import app_settings
    return PipelineManager(get_cosmos_db(),
                           pipelines_container_name=app_settings.COSMOS_DB_CONTAINER_PIPELINES,
                           step_catalog_container_name=app_settings.COSMOS_DB_CONTAINER_STEP_CATALOG,
                           step_instances_container_name=app_settings.COSMOS_DB_CONTAINER_STEP_INSTANCES,
                           service_catalog_container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_CATALOG,
                           service_instances_container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_INSTANCES)

@lru_cache(maxsize=1)
def get_execution_manager() -> ExecutionManager:
    """Get ExecutionManager instance"""
    from app.settings import app_settings
    return ExecutionManager(db=get_cosmos_db(), 
                            pipeline_manager=get_pipeline_manager(), 
                            batch_executions_container_name=app_settings.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS,
                            pipeline_executions_container_name=app_settings.COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS
                           )
