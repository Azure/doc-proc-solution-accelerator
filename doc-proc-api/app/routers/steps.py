from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.models.step import StepInstanceCreateRequest, StepInstanceUpdateRequest, StepInstance, StepCatalogDefinition
from app.services.step_catalog_service import StepCatalogService
from app.services.step_instance_service import StepInstanceService
from app.dependencies import get_step_catalog_service, get_step_instance_service
from app.exceptions import ApiException

router = APIRouter(prefix="/api/steps", tags=["steps"])

#######################################################
# Step Catalog endpoints
@router.get("/catalog", response_model=List[StepCatalogDefinition])
async def list_step_catalog(service: StepCatalogService = Depends(get_step_catalog_service)):
    """List all steps from the step catalog"""
    catalog_steps = await service.list_catalog_steps()
    return [StepCatalogDefinition(**step) for step in catalog_steps]

@router.get("/catalog/{step_catalog_id}", response_model=StepCatalogDefinition)
async def get_catalog_step(step_catalog_id: str, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Get a specific step from the catalog by ID"""
    catalog_step = await service.get_catalog_step_by_id(step_catalog_id)
    if not catalog_step:
        raise ApiException(status_code=404, message="Step definition not found in catalog")
    return StepCatalogDefinition(**catalog_step)

@router.post("/initialize")
async def initialize_catalog_steps(service: StepCatalogService = Depends(get_step_catalog_service)):
    """Initialize default steps from catalog"""
    return await service.initialize_step_catalog()

#######################################################
# Step Instance endpoints
@router.get("/instances", response_model=List[StepInstance])
async def list_step_instances(service: StepInstanceService = Depends(get_step_instance_service)):
    """List all step instances"""
    items = await service.list_all()
    return [StepInstance(**item) for item in items]


@router.get("/instances/{id}", response_model=StepInstance)
async def get_step_instance(id: str, service: StepInstanceService = Depends(get_step_instance_service)):
    """Get a specific step instance by ID"""
    item = await service.get_by_id(id)
    if not item:
        raise ApiException(status_code=404, message=f"Step instance with id '{id}' not found")
    return StepInstance(**item)

@router.post("/instances", response_model=StepInstance)
async def create_step_instance(step_instance_data: StepInstanceCreateRequest, service: StepInstanceService = Depends(get_step_instance_service)):
    """Create a new step instance"""
    try:
        saved = await service.create_step_instance(step_instance_data.model_dump())
        return StepInstance(**saved)
    except Exception as e:
        raise ApiException(status_code=400, message=f"Failed to create step instance", details=str(e))

@router.put("/instances/{id}", response_model=StepInstance)
async def update_step_instance(id: str, step_instance_data: StepInstanceUpdateRequest, service: StepInstanceService = Depends(get_step_instance_service)):
    """Update an existing step instance"""
    existing = await service.get_by_id(id)
    if not existing:
        raise ApiException(status_code=404, message="Step instance not found")
    
    try:
        saved = await service.update_step_instance(id, step_instance_data.model_dump(exclude_unset=True))
        return StepInstance(**saved)
    except Exception as e:
        raise ApiException(status_code=400, message="Failed to update step instance", details=str(e))

@router.delete("/instances/{id}")
async def delete_step_instance(id: str, service: StepInstanceService = Depends(get_step_instance_service)):
    """Delete a step instance"""
    
    try:
        success = await service.delete_step_instance(id)
        if not success:
            raise ApiException(status_code=404, message="Step instance not found or failed to delete")
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=400, message="Failed to delete step instance", details=str(e))
    
    return {"message": "Step instance deleted successfully"}
