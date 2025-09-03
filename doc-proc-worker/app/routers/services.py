from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.models.service import Service, ServiceInstance, ServiceCatalogDefinition
from app.services.servicecatalog_service import ServiceCatalogService
from app.dependencies import get_service_catalog_service

router = APIRouter()


@router.get("/catalog", response_model=List[ServiceCatalogDefinition])
async def list_service_catalog(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """List all services from the service catalog"""
    catalog_services = await service.list_catalog_services()
    return [ServiceCatalogDefinition(**svc) for svc in catalog_services]


@router.get("/catalog/{service_id}", response_model=ServiceCatalogDefinition)
async def get_catalog_service(service_id: str, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Get a specific service from the catalog by ID"""
    catalog_service = await service.get_catalog_service_by_id(service_id)
    if not catalog_service:
        raise HTTPException(status_code=404, detail="Service not found in catalog")
    return ServiceCatalogDefinition(**catalog_service)


@router.get("/", response_model=List[ServiceInstance])
async def list_service_instances(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """List all service instances"""
    items = await service.list_all()
    return [ServiceInstance(**item) for item in items]


@router.get("/{id}", response_model=ServiceInstance)
async def get_service_instance(id: str, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Get a specific service instance by ID"""
    item = await service.get_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail="Service instance not found")
    return ServiceInstance(**item)


@router.post("/", response_model=ServiceInstance)
async def create_service_instance(service_data: ServiceInstance, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Create a new service instance"""
    service_data.touch()
    try:
        saved = await service.create_service_instance(service_data.model_dump())
        return ServiceInstance(**saved)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=ServiceInstance)
async def update_service_instance(id: str, service_data: ServiceInstance, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Update an existing service instance"""
    if id != service_data.id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    service_data.touch()
    saved = await service.update(service_data.model_dump())
    return ServiceInstance(**saved)


@router.delete("/{id}")
async def delete_service_instance(id: str, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Delete a service instance"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Service instance not found")
    return {"message": "Service instance deleted successfully"}


@router.get("/type/{service_type}", response_model=List[ServiceInstance])
async def get_services_by_type(service_type: str, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Get all service instances of a specific type"""
    items = await service.get_services_by_type(service_type)
    return [ServiceInstance(**item) for item in items]


# # Legacy endpoints for backward compatibility
# @router.post("/legacy", response_model=Service)
# async def create_legacy_service(service_data: Service, service: ServiceCatalogService = Depends(get_service_catalog_service)):
#     """Create a legacy service (backward compatibility)"""
#     service_data.touch()
#     saved = await service.create(service_data.model_dump())
#     return Service(**saved)


# @router.get("/legacy/{id}", response_model=Service)
# async def get_legacy_service(id: str, service: ServiceCatalogService = Depends(get_service_catalog_service)):
#     """Get a legacy service by ID (backward compatibility)"""
#     item = await service.get_by_id(id)
#     if not item:
#         raise HTTPException(status_code=404, detail="Service not found")
#     return Service(**item)
