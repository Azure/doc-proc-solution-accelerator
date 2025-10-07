from functools import lru_cache

from app.proxy.cosmos import CosmosDb
from app.proxy.queue import StorageQueue

from doc.proc.utils.ttl_cache import ttl_cache
from doc.proc.providers.config_provider import ConfigurationProvider

# Ensure doc-proc-lib source classes are available
try:
    from doc.proc.source.source_base import SourceBase
    from doc.proc.source.source_instance_loader import create_source_instance
    from doc.proc.source.source_config import SourceConfig
except ImportError as e:
    print(f"Warning: Could not import doc-proc-lib source classes: {e}")
    # These will be handled gracefully in the source manager


__config: ConfigurationProvider = None

def get_config_provider(refresh: bool = False) -> ConfigurationProvider:
    """Get a singleton instance of ConfigurationProvider"""
    global __config
    if __config is None:
        __config = ConfigurationProvider(config_key_filters=["doc-proc.crawler.*"])
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

def get_cosmos_proxy() -> CosmosDb:
    """Alias for get_cosmos_db for compatibility"""
    return get_cosmos_db()

def get_storage_queue_proxy() -> StorageQueue:
    """Get a singleton instance of StorageQueue"""
    from app.settings import app_settings

    if not app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL or not app_settings.STORAGE_WORKER_QUEUE_NAME:
        raise RuntimeError("Storage Queue URL and Queue Name must be configured")

    return StorageQueue(storage_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                        queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME)