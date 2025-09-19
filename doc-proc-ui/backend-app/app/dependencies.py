from functools import lru_cache

from app.db.cosmos import CosmosDb
from app.services.service_catalog_service import ServiceCatalogService
from app.services.service_instance_service import ServiceInstanceService
from app.services.step_catalog_service import StepCatalogService
from app.services.step_instance_service import StepInstanceService

from app.services.pipeline_service import PipelineService
# from app.services.execution_service import ExecutionService
from app.services.vault_service import VaultService
from app.services.vault_documents_service import VaultDocumentsService
from app.services.dashboard_service import DashboardService

from app.settings import app_settings

@lru_cache(maxsize=1)
def get_cosmos_db() -> CosmosDb:
    """Get a singleton instance of CosmosDb"""
    return CosmosDb(
        endpoint=app_settings.COSMOS_DB_ENDPOINT,
        db_name=app_settings.COSMOS_DB_NAME,
        initial_containers=app_settings.get_cosmos_db_containers()
    )

def get_service_catalog_service() -> ServiceCatalogService:
    """Get ServiceCatalogService instance"""
    return ServiceCatalogService(db=get_cosmos_db(), 
                                 container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_CATALOG)

def get_service_instance_service() -> ServiceInstanceService:
    """Get ServiceInstanceService instance"""
    return ServiceInstanceService(db=get_cosmos_db(), 
                                  container_name=app_settings.COSMOS_DB_CONTAINER_SERVICE_INSTANCES,
                                  catalog_service=get_service_catalog_service())

def get_step_catalog_service() -> StepCatalogService:
    """Get StepCatalogService instance"""
    return StepCatalogService(db=get_cosmos_db(),
                              container_name=app_settings.COSMOS_DB_CONTAINER_STEP_CATALOG)

def get_step_instance_service() -> StepInstanceService:
    """Get StepInstanceService instance"""
    return StepInstanceService(db=get_cosmos_db(),
                               container_name=app_settings.COSMOS_DB_CONTAINER_STEP_INSTANCES,
                               catalog_service=get_step_catalog_service())


def get_pipeline_service() -> PipelineService:
    """Get PipelineService instance"""
    return PipelineService(db=get_cosmos_db())


# def get_execution_service() -> ExecutionService:
#     """Get ExecutionService instance"""
#     return ExecutionService(get_cosmos_db())

def get_storage_queue_helper():
    """Get StorageQueueHelper instance"""
    from app.services.storage_queue_helper import StorageQueueHelper
    return StorageQueueHelper(storage_queue_url=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
                              queue_name=app_settings.STORAGE_WORKER_QUEUE_NAME)


def get_vault_documents_service() -> VaultDocumentsService:
    """Get VaultDocumentsService instance"""
    return VaultDocumentsService(db=get_cosmos_db(),
                                  container_name=app_settings.COSMOS_DB_CONTAINER_VAULT_DOCUMENTS,
                                  storage_queue_helper=get_storage_queue_helper())


def get_vault_service() -> VaultService:
    """Get VaultService instance"""
    return VaultService(db=get_cosmos_db(), 
                        container_name=app_settings.COSMOS_DB_CONTAINER_VAULTS,
                        vault_documents_service=get_vault_documents_service(),
                        default_blob_storage=app_settings.get_blob_storage_account_details())


def get_dashboard_service() -> DashboardService:
    """Get DashboardService instance"""
    return DashboardService(db=get_cosmos_db())
