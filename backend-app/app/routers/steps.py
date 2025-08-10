from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ..models.step import Step, StepInstance, StepCatalogDefinition
from ..services.step_service import StepCatalogService
from ..dependencies import get_step_catalog_service

router = APIRouter()


@router.get("/catalog", response_model=List[StepCatalogDefinition])
async def list_step_catalog(service: StepCatalogService = Depends(get_step_catalog_service)):
    """List all steps from the step catalog"""
    catalog_steps = await service.list_catalog_steps()
    return [StepCatalogDefinition(**step) for step in catalog_steps]


@router.get("/catalog/{step_id}", response_model=StepCatalogDefinition)
async def get_catalog_step(step_id: str, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Get a specific step from the catalog by ID"""
    catalog_step = await service.get_catalog_step_by_id(step_id)
    if not catalog_step:
        raise HTTPException(status_code=404, detail="Step not found in catalog")
    return StepCatalogDefinition(**catalog_step)


@router.get("/catalog/category/{category}", response_model=List[StepCatalogDefinition])
async def get_steps_by_category(category: str, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Get all steps from catalog by category"""
    steps = await service.get_steps_by_category(category)
    return [StepCatalogDefinition(**step) for step in steps]


@router.post("/catalog/tags", response_model=List[StepCatalogDefinition])
async def get_steps_by_tags(tags: List[str], service: StepCatalogService = Depends(get_step_catalog_service)):
    """Get all steps from catalog that match any of the provided tags"""
    steps = await service.get_steps_by_tags(tags)
    return [StepCatalogDefinition(**step) for step in steps]


@router.get("/", response_model=List[StepInstance])
async def list_step_instances(service: StepCatalogService = Depends(get_step_catalog_service)):
    """List all step instances"""
    items = await service.list_all()
    return [StepInstance(**item) for item in items]


@router.get("/{id}", response_model=StepInstance)
async def get_step_instance(id: str, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Get a specific step instance by ID"""
    item = await service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Step instance not found")
    return StepInstance(**item)


@router.post("/", response_model=StepInstance)
async def create_step_instance(step_data: StepInstance, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Create a new step instance"""
    step_data.touch()
    try:
        saved = await service.create_step_instance(step_data.model_dump())
        return StepInstance(**saved)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=StepInstance)
async def update_step_instance(id: str, step_data: StepInstance, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Update an existing step instance"""
    if id != step_data.id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    step_data.touch()
    saved = await service.update(step_data.model_dump())
    return StepInstance(**saved)


@router.delete("/{id}")
async def delete_step_instance(id: str, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Delete a step instance"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Step instance not found")
    return {"message": "Step instance deleted successfully"}


# Legacy endpoints for backward compatibility
@router.post("/legacy", response_model=Step)
async def create_legacy_step(step_data: Step, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Create a legacy step (backward compatibility)"""
    step_data.touch()
    saved = await service.create(step_data.model_dump())
    return Step(**saved)


@router.get("/legacy/{id}", response_model=Step)
async def get_legacy_step(id: str, service: StepCatalogService = Depends(get_step_catalog_service)):
    """Get a legacy step by ID (backward compatibility)"""
    item = await service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Step not found")
    return Step(**item)
