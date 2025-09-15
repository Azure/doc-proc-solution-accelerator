from functools import lru_cache

from app.db.cosmos import CosmosDb
from app.services.cosmos_db_service import CosmosDBService
from app.services.pipeline_service import PipelineService
from app.services.execution_service import ExecutionService
from app.services.queue_service import AzureStorageQueueService
from app.services.activity_log_service import ActivityLogService

from app.settings import app_settings

@lru_cache()
def get_cosmos_db() -> CosmosDb:
    """Get a singleton instance of CosmosDb"""
    return CosmosDb(endpoint=app_settings.COSMOS_DB_ENDPOINT)

def get_cosmos_db_service(container_name: str) -> CosmosDBService:
    """Get CosmosDBService instance"""
    return CosmosDBService(get_cosmos_db(), container_name=container_name)

def get_pipeline_service() -> PipelineService:
    """Get PipelineService instance"""
    return PipelineService(get_cosmos_db())

def get_activity_log_service() -> ActivityLogService:
    """Get ActivityLogService instance"""
    return ActivityLogService(get_cosmos_db())

def get_execution_service() -> ExecutionService:
    """Get ExecutionService instance"""
    return ExecutionService(get_cosmos_db(), get_pipeline_service(), get_activity_log_service())

def get_queue_service() -> AzureStorageQueueService:
    """Get AzureStorageQueueService instance"""
    return AzureStorageQueueService()