from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.models.source import (
    SourceInstance, 
    SourceCatalogDefinition,
    SourceInstanceCreateRequest,
    SourceInstanceUpdateRequest,
    SourceTestConnectionResponse
)
from app.services.source_catalog_service import SourceCatalogService
from app.services.source_instance_service import SourceInstanceService
from app.dependencies import get_source_catalog_service, get_source_instance_service
from app.exceptions import ApiException

router = APIRouter(prefix="/api/sources", tags=["sources"])

#######################################################
# Source Catalog endpoints
@router.get("/catalog", response_model=List[SourceCatalogDefinition])
async def list_source_catalog(service: SourceCatalogService = Depends(get_source_catalog_service)):
    """List all sources from the source catalog"""
    catalog_sources = await service.list_catalog_sources()
    return [SourceCatalogDefinition(**src) for src in catalog_sources]


@router.get("/catalog/{source_id}", response_model=SourceCatalogDefinition)
async def get_catalog_source(source_id: str, service: SourceCatalogService = Depends(get_source_catalog_service)):
    """Get a specific source from the catalog by ID"""
    catalog_source = await service.get_catalog_source_by_id(source_id)
    if not catalog_source:
        raise ApiException(message="Source not found in catalog", status_code=404)
    return SourceCatalogDefinition(**catalog_source)


@router.get("/catalog/type/{source_type}", response_model=List[SourceCatalogDefinition])
async def get_sources_by_type(source_type: str, service: SourceCatalogService = Depends(get_source_catalog_service)):
    """Get all sources of a specific type from the catalog"""
    catalog_sources = await service.get_sources_by_type(source_type)
    return [SourceCatalogDefinition(**src) for src in catalog_sources]


@router.get("/catalog/tags/{tags}", response_model=List[SourceCatalogDefinition])
async def get_sources_by_tags(tags: str, service: SourceCatalogService = Depends(get_source_catalog_service)):
    """Get sources that have any of the specified tags (comma-separated)"""
    tag_list = [tag.strip() for tag in tags.split(",")]
    catalog_sources = await service.get_sources_by_tags(tag_list)
    return [SourceCatalogDefinition(**src) for src in catalog_sources]


@router.post("/initialize")
async def initialize_catalog_sources(service: SourceCatalogService = Depends(get_source_catalog_service)):
    """Initialize default sources from catalog"""
    return await service.initialize_source_catalog()


#######################################################
# Source Instance endpoints
@router.get("/instances", response_model=List[SourceInstance])
async def list_source_instances(service: SourceInstanceService = Depends(get_source_instance_service)):
    """List all source instances"""
    items = await service.get_all_non_system()
    return [SourceInstance(**item) for item in items]


@router.get("/instances/enabled", response_model=List[SourceInstance])
async def list_enabled_source_instances(service: SourceInstanceService = Depends(get_source_instance_service)):
    """List all enabled source instances"""
    items = await service.get_enabled_source_instances()
    return [SourceInstance(**item) for item in items]


@router.get("/instances/catalog/{catalog_id}", response_model=List[SourceInstance])
async def get_instances_by_catalog_id(catalog_id: str, service: SourceInstanceService = Depends(get_source_instance_service)):
    """Get all source instances for a specific catalog source"""
    items = await service.get_source_instances_by_catalog_id(catalog_id)
    return [SourceInstance(**item) for item in items]


@router.post("/instances", response_model=SourceInstance)
async def create_source_instance(source_data: SourceInstanceCreateRequest, service: SourceInstanceService = Depends(get_source_instance_service)):
    """Create a new source instance"""
    try:
        saved = await service.create_source_instance(source_data.model_dump())
        return SourceInstance(**saved)
    except Exception as e:
        raise ApiException(message="Failed to create source instance.", status_code=400, details=str(e))


@router.get("/instances/{id}", response_model=SourceInstance)
async def get_source_instance(id: str, service: SourceInstanceService = Depends(get_source_instance_service)):
    """Get a specific source instance by ID"""
    item = await service.get_by_id(id)
    if not item:
        raise ApiException(message="Source instance not found", status_code=404)
    return SourceInstance(**item)


@router.put("/instances/{id}", response_model=SourceInstance)
async def update_source_instance(id: str, source_data: SourceInstanceUpdateRequest, service: SourceInstanceService = Depends(get_source_instance_service)):
    """Update an existing source instance"""
    try:
        saved = await service.update_source_instance(id, source_data.model_dump(exclude_unset=True))
        return SourceInstance(**saved)
    except Exception as e:
        raise ApiException(message="Failed to update source instance.", status_code=400, details=str(e))


@router.delete("/instances/{id}")
async def delete_source_instance(id: str, service: SourceInstanceService = Depends(get_source_instance_service)):
    """Delete a source instance"""
    try:    
        success = await service.delete_source_instance_by_id(id)
        if not success:
            raise ApiException(message="Source instance not found or failed to delete.", status_code=404)
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(message="Failed to delete source instance.", status_code=400, details=str(e))
    
    return {"message": "Source instance deleted successfully"}


# Connection testing endpoints
@router.post("/instances/{id}/test-connection", response_model=SourceTestConnectionResponse)
async def test_source_connection(id: str, service: SourceInstanceService = Depends(get_source_instance_service)):
    """Test connection for a specific source instance"""
    try:
        result = await service.test_source_instance_connection(id)
        return SourceTestConnectionResponse(**result)
    except Exception as e:
        raise ApiException(message="Failed to test source connection.", status_code=400, details=str(e))