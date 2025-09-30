from typing import List

from fastapi import APIRouter, Depends

from app.models.pipeline import Pipeline, CreatePipelineRequest
from app.services.pipeline_service import PipelineService
from app.dependencies import get_pipeline_service
from app.exceptions import ApiException

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

@router.get("/", response_model=List[Pipeline])
async def list_pipelines(service: PipelineService = Depends(get_pipeline_service)):
    """List all pipelines"""
    return await service.list_pipelines()

@router.get("/{pipeline_id_or_name}", response_model=dict)
async def get_pipeline(pipeline_id_or_name: str, service: PipelineService = Depends(get_pipeline_service)):
    """Get a specific pipeline by ID or by Name"""
    pipeline = await service.get_pipeline_by_id(pipeline_id_or_name)
    if not pipeline:
        pipeline = await service.get_pipeline_by_name(pipeline_id_or_name)
    if not pipeline:
        raise ApiException(status_code=404, message="Pipeline not found")
    return pipeline

@router.post("/", response_model=Pipeline)
async def create_pipeline(pipeline_data: CreatePipelineRequest, service: PipelineService = Depends(get_pipeline_service)):
    """Create a new pipeline"""
    try:
        saved = await service.create_pipeline(pipeline_data.model_dump())
        return Pipeline(**saved)
    except Exception as e:
        raise ApiException(status_code=400, message="Failed to create pipeline", details=str(e))

@router.put("/{pipeline_id}", response_model=Pipeline)
async def update_pipeline(pipeline_id: str, pipeline_data: Pipeline, service: PipelineService = Depends(get_pipeline_service)):
    """Update an existing pipeline"""
    if pipeline_id != pipeline_data.id:
        raise ApiException(status_code=400, message="ID mismatch")
    pipeline_data.touch()
    saved = await service.update_by_id(pipeline_id, pipeline_data.model_dump())
    return Pipeline(**saved)

@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, service: PipelineService = Depends(get_pipeline_service)):
    """Delete a pipeline"""
    try:
        success = await service.delete_pipeline_by_id(pipeline_id)
        if not success:
            raise ApiException(status_code=404, message="Pipeline instance not found")
    
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=400, message="Failed to delete pipeline", details=str(e))
    
    return {"message": "Pipeline instance deleted successfully"}