"""
Health router for exposing health check endpoints.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.services.health_service import health_service, SystemHealth, ServiceHealth
from app.exceptions import ApiException

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/", response_model=SystemHealth)
async def health():
    """
    Detailed health check that tests all configured services.
    This endpoint checks connectivity to Cosmos DB, Azure Storage, and Azure App Configuration.
    """
    try:
        system_health = await health_service.check_all_services()
     
        return JSONResponse(
            content=system_health.model_dump(),
            status_code=200
        )
        
    except Exception as e:
        raise ApiException(status_code=503, message=f"Health check failed", details=f"{str(e)}")

@router.get("/{service_name}", response_model=ServiceHealth)
async def service_health(service_name: str):
    """
    Check the health of a specific service.
    
    Available services:
    - cosmos_db: Azure Cosmos DB connectivity
    - storage_queue: Azure Storage Queue connectivity  
    - app_config: Azure App Configuration connectivity
    """
    try:
        service_health_result = await health_service.check_service_health(service_name)
        
        return JSONResponse(
            content=service_health_result.model_dump(),
            status_code=200
        )
        
    except Exception as e:
        raise ApiException(status_code=503, message=f"Service health check failed.", details=f"{str(e)}")

