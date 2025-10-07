from functools import lru_cache

from app.db.cosmos import CosmosDb
from app.services.service_catalog_service import ServiceCatalogService
from app.services.service_instance_service import ServiceInstanceService
from app.services.step_catalog_service import StepCatalogService
from app.services.step_instance_service import StepInstanceService
from app.services.source_catalog_service import SourceCatalogService
from app.services.source_instance_service import SourceInstanceService

from app.services.pipeline_service import PipelineService
from app.services.execution_status_service import ExecutionStatusService
from app.services.vault_service import VaultService
from app.services.vault_documents_service import VaultDocumentsService
from app.services.health_service import HealthService
from app.services.dashboard_service import DashboardService

from doc.proc.utils.ttl_cache import ttl_cache
from doc.proc.providers.config_provider import ConfigurationProvider

__config: ConfigurationProvider = None

__cache_ttl: int = 60 * 10  # cache for 10 minutes for all services

def get_config_provider(refresh: bool = False) -> ConfigurationProvider:
    """Get a singleton instance of ConfigurationProvider"""
    global __config
    if __config is None:
        __config = ConfigurationProvider(config_key_filters=["doc-proc.api.*"])
    elif refresh:
        __config.request_refresh()
    return __config

@ttl_cache(maxsize=1, ttl=__cache_ttl)
def get_cosmos_db() -> CosmosDb:
    """Get a singleton instance of CosmosDb"""
    from app.settings import get_settings
    app_settings = get_settings()
    return CosmosDb(
        endpoint=app_settings.COSMOS_DB_ENDPOINT,
        db_name=app_settings.COSMOS_DB_NAME,
        initial_containers=app_settings.get_cosmos_db_containers()
    )

@ttl_cache(maxsize=1, ttl=__cache_ttl)
def get_service_catalog_service() -> ServiceCatalogService:
    """Get ServiceCatalogService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return ServiceCatalogService(db=get_cosmos_db(), 
                                 container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_CATALOG)

@ttl_cache(maxsize=1, ttl=__cache_ttl)
def get_service_instance_service() -> ServiceInstanceService:
    """Get ServiceInstanceService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return ServiceInstanceService(db=get_cosmos_db(), 
                                  container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_INSTANCES,
                                  catalog_service=get_service_catalog_service())

@ttl_cache(maxsize=1, ttl=__cache_ttl)
def get_step_catalog_service() -> StepCatalogService:
    """Get StepCatalogService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return StepCatalogService(db=get_cosmos_db(),
                              container_name=app_settings.COSMOS_DB_CONTAINER_STEP_CATALOG)

@ttl_cache(maxsize=1, ttl=__cache_ttl)
def get_step_instance_service() -> StepInstanceService:
    """Get StepInstanceService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return StepInstanceService(db=get_cosmos_db(),
                               container_name=app_settings.COSMOS_DB_CONTAINER_STEP_INSTANCES,
                               catalog_service=get_step_catalog_service())

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_pipeline_service() -> PipelineService:
    """Get PipelineService instance"""
    return PipelineService(db=get_cosmos_db())

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_execution_status_service() -> ExecutionStatusService:
    """Get PipelineExecutionService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return ExecutionStatusService(db=get_cosmos_db(), 
                                    pipeline_executions_container=app_settings.COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS,
                                    vault_documents_container=app_settings.COSMOS_DB_CONTAINER_VAULT_DOCUMENTS,
                                    batch_executions_container=app_settings.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS)

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_document_queue_submitter():
    """Get DocumentQueueSubmitter instance"""
    from app.settings import get_settings
    from app.services.document_queue_submitter import DocumentQueueSubmitter
    app_settings = get_settings()
    return DocumentQueueSubmitter(storage_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                                  queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME)

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_vault_documents_service() -> VaultDocumentsService:
    """Get VaultDocumentsService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return VaultDocumentsService(db=get_cosmos_db(),
                                  container_name=app_settings.COSMOS_DB_CONTAINER_VAULT_DOCUMENTS,
                                  document_queue_submitter=get_document_queue_submitter())

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 30 minutes
def get_vault_service() -> VaultService:
    """Get VaultService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return VaultService(db=get_cosmos_db(), 
                        container_name=app_settings.COSMOS_DB_CONTAINER_VAULTS,
                        vault_documents_service=get_vault_documents_service(),
                        execution_status_service=get_execution_status_service(),
                        default_blob_storage=app_settings.get_blob_storage_account_details())

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_dashboard_service() -> DashboardService:
    """Get DashboardService instance"""
    return DashboardService(db=get_cosmos_db())

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_source_catalog_service() -> SourceCatalogService:
    """Get SourceCatalogService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return SourceCatalogService(db=get_cosmos_db(), 
                                container_name=app_settings.COSMOS_DB_CONTAINER_SOURCE_CATALOG)

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_source_instance_service() -> SourceInstanceService:
    """Get SourceInstanceService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return SourceInstanceService(db=get_cosmos_db(), 
                                 container_name=app_settings.COSMOS_DB_CONTAINER_SOURCE_INSTANCES,
                                 catalog_service=get_source_catalog_service(),
                                 vault_service=get_vault_service())

@ttl_cache(maxsize=1, ttl=__cache_ttl)  # Cache for 10 minutes
def get_health_service() -> HealthService:
    """Get HealthService instance"""
    from app.settings import get_settings
    app_settings = get_settings()
    return HealthService(cosmos_endpoint=app_settings.COSMOS_DB_ENDPOINT,
                         cosmos_db_name=app_settings.COSMOS_DB_NAME,
                         cosmos_db_containers=app_settings.get_cosmos_db_containers(),
                         blob_storage_account=app_settings.BLOB_STORAGE_ACCOUNT_NAME,
                         blob_storage_container=app_settings.BLOB_STORAGE_CONTAINER_NAME,
                         storage_account_worker_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                         storage_worker_queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME)