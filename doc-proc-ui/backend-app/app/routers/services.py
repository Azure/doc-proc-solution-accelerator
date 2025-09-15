from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.models.service import (
    ServiceInstance, 
    ServiceCatalogDefinition,
    ServiceCreateRequest,
    ServiceUpdateRequest,
    ServiceTestConnectionResponse
)
from app.services.service_catalog_service import ServiceCatalogService
from app.services.service_instance_service import ServiceInstanceService
from app.dependencies import get_service_catalog_service, get_service_instance_service
from app.exceptions import ApiException

router = APIRouter(prefix="/api/services", tags=["services"])

#######################################################
# Service Catalog endpoints
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
        raise ApiException(message="Service not found in catalog", status_code=404)
    return ServiceCatalogDefinition(**catalog_service)

@router.post("/initialize")
async def initialize_catalog_services(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    """Initialize default services from catalog"""
    return await service.initialize_service_catalog()

#######################################################
# Service Instance endpoints
@router.get("/instances", response_model=List[ServiceInstance])
async def list_service_instances(service: ServiceInstanceService = Depends(get_service_instance_service)):
    """List all service instances"""
    items = await service.list_all()
    return [ServiceInstance(**item) for item in items]

@router.post("/instances", response_model=ServiceInstance)
async def create_service_instance(service_data: ServiceCreateRequest, service: ServiceInstanceService = Depends(get_service_instance_service)):
    """Create a new service instance"""
    try:
        saved = await service.create_service_instance(service_data.model_dump())
        return ServiceInstance(**saved)
    except Exception as e:
        raise ApiException(message="Failed to create service instance.", status_code=400, details=str(e))

@router.get("/instances/{id}", response_model=ServiceInstance)
async def get_service_instance(id: str, service: ServiceInstanceService = Depends(get_service_instance_service)):
    """Get a specific service instance by ID"""
    item = await service.get_by_id(id)
    if not item:
        raise ApiException(message="Service instance not found", status_code=404)
    return ServiceInstance(**item)


@router.put("/instances/{id}", response_model=ServiceInstance)
async def update_service_instance(id: str, service_data: ServiceUpdateRequest, service: ServiceInstanceService = Depends(get_service_instance_service)):
    """Update an existing service instance"""
    try:
        saved = await service.update_service_instance(id, service_data.model_dump(exclude_unset=True))
        return ServiceInstance(**saved)
    except Exception as e:
        raise ApiException(message="Failed to update service instance.", status_code=400, details=str(e))


@router.delete("/instances/{id}")
async def delete_service_instance(id: str, service: ServiceInstanceService = Depends(get_service_instance_service)):
    """Delete a service instance"""
    success = await service.delete(id)
    if not success:
        raise ApiException(message="Service instance not found or failed to delete.", status_code=404)
    return {"message": "Service instance deleted successfully"}


# Connection testing endpoints
@router.post("/instances/{id}/test-connection", response_model=ServiceTestConnectionResponse)
async def test_service_connection(id: str, service: ServiceInstanceService = Depends(get_service_instance_service)):
    """Test connection for a specific service instance"""
    try:
        result = await service.test_service_connection(id)
        return ServiceTestConnectionResponse(**result)
    except ValueError as e:
        raise ApiException(message="Service instance not found", status_code=404, details=str(e))
    except Exception as e:
        raise ApiException(message=f"Connection test failed: {str(e)}", status_code=500)

