from functools import lru_cache

from app.proxy.cosmos import CosmosDb
from app.proxy.queue import StorageQueue
from app.managers.pipeline_manager import PipelineManager
from app.managers.execution_manager import ExecutionManager

from doc.proc.utils.ttl_cache import ttl_cache
from doc.proc.providers.config_provider import ConfigurationProvider


__config: ConfigurationProvider = None

def get_config_provider(refresh: bool = False) -> ConfigurationProvider:
    """Get a singleton instance of ConfigurationProvider"""
    global __config
    if __config is None:
        __config = ConfigurationProvider(config_key_filters=["doc-proc.worker.*"])
    elif refresh:
        __config.request_refresh()
    return __config

@ttl_cache(maxsize=1, ttl=60 * 60)  # Cache for 1 hour
def get_cosmos_db() -> CosmosDb:
    """Get a singleton instance of CosmosDb"""
    from app.settings import app_settings
    return CosmosDb(endpoint=app_settings.COSMOS_DB_ENDPOINT,
                    database_name=app_settings.COSMOS_DB_NAME,
                    init_containers=app_settings.get_cosmos_db_containers())

@ttl_cache(maxsize=1, ttl=60 * 60)  # Cache for 1 hour
def get_queue_proxy() -> StorageQueue:
    """Get StorageQueue instance"""
    from app.settings import app_settings
    return StorageQueue(storage_account_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                        queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME)

@ttl_cache(maxsize=1, ttl=-1)  # Cache indefinitely
def get_pipeline_manager() -> PipelineManager:
    """Get PipelineManager instance"""
    from app.settings import app_settings
    return PipelineManager(get_cosmos_db(),
                           pipelines_container_name=app_settings.COSMOS_DB_CONTAINER_PIPELINES,
                           step_catalog_container_name=app_settings.COSMOS_DB_CONTAINER_STEP_CATALOG,
                           step_instances_container_name=app_settings.COSMOS_DB_CONTAINER_STEP_INSTANCES,
                           service_catalog_container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_CATALOG,
                           service_instances_container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_INSTANCES,
                           source_catalog_container_name=app_settings.COSMOS_DB_CONTAINER_SOURCE_CATALOG,
                           source_instances_container_name=app_settings.COSMOS_DB_CONTAINER_SOURCE_INSTANCES)

@ttl_cache(maxsize=1, ttl=-1)  # Cache indefinitely
def get_execution_manager() -> ExecutionManager:
    """Get ExecutionManager instance"""
    from app.settings import app_settings
    return ExecutionManager(db=get_cosmos_db(), 
                            pipeline_manager=get_pipeline_manager(), 
                            batch_executions_container_name=app_settings.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS,
                            pipeline_executions_container_name=app_settings.COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS
                           )
