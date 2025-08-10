from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ..models.pipeline import Pipeline, PipelineInstance, PipelineStepDefinition
from ..services.pipeline_service import PipelineService
from ..dependencies import get_pipeline_service

router = APIRouter()


@router.get("/config", response_model=List[dict])
async def list_pipeline_configurations(service: PipelineService = Depends(get_pipeline_service)):
    """List all pipeline configurations from YAML"""
    return await service.list_config_pipelines()


@router.get("/config/{pipeline_name}", response_model=dict)
async def get_pipeline_configuration(pipeline_name: str, service: PipelineService = Depends(get_pipeline_service)):
    """Get a specific pipeline configuration by name"""
    config_pipeline = await service.get_pipeline_by_name(pipeline_name)
    if not config_pipeline:
        raise HTTPException(status_code=404, detail="Pipeline configuration not found")
    return config_pipeline


@router.get("/service-instances", response_model=List[dict])
async def get_service_instances(service: PipelineService = Depends(get_pipeline_service)):
    """Get all service instances from configuration"""
    return await service.get_service_instances()


@router.get("/", response_model=List[PipelineInstance])
async def list_pipeline_instances(service: PipelineService = Depends(get_pipeline_service)):
    """List all pipeline instances"""
    items = await service.list_all()
    return [PipelineInstance(**item) for item in items]


@router.get("/{id}", response_model=PipelineInstance)
async def get_pipeline_instance(id: str, service: PipelineService = Depends(get_pipeline_service)):
    """Get a specific pipeline instance by ID"""
    item = await service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline instance not found")
    return PipelineInstance(**item)


@router.post("/", response_model=PipelineInstance)
async def create_pipeline_instance(pipeline_data: PipelineInstance, service: PipelineService = Depends(get_pipeline_service)):
    """Create a new pipeline instance"""
    pipeline_data.touch()
    try:
        saved = await service.create_pipeline_instance(pipeline_data.model_dump())
        return PipelineInstance(**saved)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=PipelineInstance)
async def update_pipeline_instance(id: str, pipeline_data: PipelineInstance, service: PipelineService = Depends(get_pipeline_service)):
    """Update an existing pipeline instance"""
    if id != pipeline_data.id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    pipeline_data.touch()
    saved = await service.update(pipeline_data.model_dump())
    return PipelineInstance(**saved)


@router.delete("/{id}")
async def delete_pipeline_instance(id: str, service: PipelineService = Depends(get_pipeline_service)):
    """Delete a pipeline instance"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Pipeline instance not found")
    return {"message": "Pipeline instance deleted successfully"}


@router.get("/{id}/steps", response_model=List[PipelineStepDefinition])
async def get_pipeline_steps(id: str, service: PipelineService = Depends(get_pipeline_service)):
    """Get all steps for a specific pipeline"""
    steps = await service.get_pipeline_steps(id)
    return [PipelineStepDefinition(**step) for step in steps]


@router.patch("/{id}/status")
async def update_pipeline_status(id: str, status: str, service: PipelineService = Depends(get_pipeline_service)):
    """Update pipeline status"""
    pipeline = await service.update_pipeline_status(id, status)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline instance not found")
    return {"message": f"Pipeline status updated to {status}"}


@router.get("/status/{status}", response_model=List[PipelineInstance])
async def get_pipelines_by_status(status: str, service: PipelineService = Depends(get_pipeline_service)):
    """Get all pipelines with a specific status"""
    items = await service.get_pipelines_by_status(status)
    return [PipelineInstance(**item) for item in items]

