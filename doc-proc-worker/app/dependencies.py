from functools import lru_cache

from app.db.cosmos import CosmosDb
from app.services.servicecatalog_service import ServiceCatalogService
from app.services.step_service import StepCatalogService
from app.services.pipeline_service import PipelineService
from app.services.execution_service import ExecutionService

@lru_cache()
def get_cosmos_db() -> CosmosDb:
    """Get a singleton instance of CosmosDb"""
    return CosmosDb()

def get_service_catalog_service() -> ServiceCatalogService:
    """Get ServiceCatalogService instance"""
    return ServiceCatalogService(get_cosmos_db())


def get_step_catalog_service() -> StepCatalogService:
    """Get StepCatalogService instance"""
    return StepCatalogService(get_cosmos_db())


def get_pipeline_service() -> PipelineService:
    """Get PipelineService instance"""
    return PipelineService(get_cosmos_db())


def get_execution_service() -> ExecutionService:
    """Get ExecutionService instance"""
    return ExecutionService(get_cosmos_db())
