"""
Health service for checking the status of various system components.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

from azure.cosmos import CosmosClient
from azure.storage.queue import QueueServiceClient
from azure.appconfiguration import AzureAppConfigurationClient
from azure.core.exceptions import ServiceRequestError, ResourceNotFoundError
from pydantic import BaseModel

from app.settings import app_settings
from app.utils import get_azure_credential, get_azure_credential_with_details

logger = logging.getLogger("doc-proc-ui.app.services.health_service")

class ServiceHealth(BaseModel):
    """Model for individual service health status"""
    name: str
    status: str  # "connected", "error"
    message: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    last_checked: str
    endpoint: Optional[str] = None
    

class SystemHealth(BaseModel):
    """Model for overall system health"""
    status: str  # "connected", "error", "degraded"
    services: Dict[str, ServiceHealth]
    checked_at: str
    summary: Dict[str, int]

class HealthService:
    """Service for checking the health of system components"""
    
    def __init__(self):
        self.cosmos_client: Optional[CosmosClient] = None
        self.queue_client: Optional[QueueServiceClient] = None
        self.app_config_client: Optional[AzureAppConfigurationClient] = None
        
    async def check_all_services(self) -> SystemHealth:
        """Check the health of all configured services"""
        services = {}
        
        # Run all health checks concurrently
        results = await asyncio.gather(
            self._check_app_config_health(),
            self._check_cosmos_db_health(),
            self._check_storage_queue_health(),
            return_exceptions=True
        )
        
        service_names = ["app_config", "cosmos_db", "storage_queue"]
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                services[service_names[i]] = ServiceHealth(
                    name=service_names[i],
                    status="error",
                    message=f"Health check failed: {result.__class__.__name__}",
                    error=f'{str(result)}',
                    last_checked=datetime.now(timezone.utc).isoformat()
                )
            else:
                services[service_names[i]] = result
        
        # Determine overall system health
        statuses = [service.status for service in services.values()]
        if all(status == "connected" for status in statuses):
            overall_status = "connected"
        elif all(status == "error" for status in statuses):
            overall_status = "error"
        else:
            overall_status = "degraded"
        
        # Create summary
        summary = {
            "connected": sum(1 for s in statuses if s == "connected"),
            "error": sum(1 for s in statuses if s == "error"),
            "total": len(statuses)
        }
        
        return SystemHealth(
            status=overall_status,
            services=services,
            checked_at=datetime.now(timezone.utc).isoformat(),
            summary=summary
        )
    
    async def _check_cosmos_db_health(self) -> ServiceHealth:
        """Check Cosmos DB connection health"""
        start_time = datetime.now(timezone.utc)
        
        try:
            if not app_settings.COSMOS_DB_ENDPOINT:
                return ServiceHealth(
                    name="cosmos_db",
                    status="error",
                    message="Cosmos DB endpoint not configured",
                    error="Cosmos DB endpoint not configured in Azure App Configuration. Ensure 'COSMOS_DB_ENDPOINT' is set using the correct key prefix.",
                    last_checked=datetime.now(timezone.utc).isoformat(),
                    endpoint="Not configured"
                )
            
            credential, token_details = get_azure_credential_with_details()
            
            # Create client if not exists
            if not self.cosmos_client:
                self.cosmos_client = CosmosClient(
                    url=app_settings.COSMOS_DB_ENDPOINT,
                    credential=credential
                )
            
            # Try to get database info
            database = self.cosmos_client.get_database_client(app_settings.COSMOS_DB_NAME)
            
            # Simple read operation to test connectivity
            database_properties = database.read()

            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return ServiceHealth(
                name="cosmos_db",
                status="connected",
                message="Connected successfully",
                details={
                    "database_name": app_settings.COSMOS_DB_NAME,
                    "database_id": database_properties.get("id"),
                    "container_count": len(app_settings.get_cosmos_db_containers()),
                    "credential_type": "default_azure_credential",
                    "credential_details": token_details
                },
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=app_settings.COSMOS_DB_ENDPOINT
            )
            
        except ResourceNotFoundError:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="cosmos_db",
                status="error",
                message="Database not found",
                error=f"Database '{app_settings.COSMOS_DB_NAME}' not found",
                details={"error_type": "ResourceNotFoundError"},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=app_settings.COSMOS_DB_ENDPOINT
            )
        except Exception as e:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="cosmos_db",
                status="error",
                message=f"Connection failed: {e.__class__.__name__}",
                error=f'{str(e)}',
                details={"error_type": type(e).__name__},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=app_settings.COSMOS_DB_ENDPOINT
            )
    
    async def _check_storage_queue_health(self) -> ServiceHealth:
        """Check Azure Storage Queue connection health"""
        start_time = datetime.now(timezone.utc)
        
        try:
            
            logger.debug(f"Checking storage queue health with URL: {app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL} and queue name: {app_settings.STORAGE_WORKER_QUEUE_NAME}")
            
            if not app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL:
                return ServiceHealth(
                    name="storage_queue",
                    status="error",
                    message="Storage queue URL not configured",
                    error="Storage queue URL not configured in Azure App Configuration. Ensure 'STORAGE_ACCOUNT_WORKER_QUEUE_URL' is set using the correct key prefix.",
                    last_checked=datetime.now(timezone.utc).isoformat(),
                    endpoint="Not configured"
                )
            
            credential, token_details = get_azure_credential_with_details()
            # Create client if not exists
            if not self.queue_client:
                # Extract account URL from queue URL
                account_url = app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL
                
                self.queue_client = QueueServiceClient(
                    account_url=account_url,
                    credential=credential
                )
            
            # Try to get queue properties
            queue_client = self.queue_client.get_queue_client(app_settings.STORAGE_WORKER_QUEUE_NAME)
            properties = queue_client.get_queue_properties()

            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return ServiceHealth(
                name="storage_queue",
                status="connected",
                message="Connected successfully",
                details={
                    "queue_name": app_settings.STORAGE_WORKER_QUEUE_NAME,
                    "approximate_message_count": properties.approximate_message_count,
                    "metadata": properties.metadata,
                    "credential_type": "default_azure_credential",
                    "credential_details": token_details
                },
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL
            )
            
        except ResourceNotFoundError:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="storage_queue",
                status="error",
                message=f"Queue '{app_settings.STORAGE_WORKER_QUEUE_NAME}' not found",
                error=f"Queue '{app_settings.STORAGE_WORKER_QUEUE_NAME}' not found",
                details={"error_type": "ResourceNotFoundError"},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL
            )
        except Exception as e:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="storage_queue",
                status="error",
                message=f"Connection failed: {e.__class__.__name__}",
                error=f'{str(e)}',
                details={"error_type": type(e).__name__},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL
            )
    
    async def _check_app_config_health(self) -> ServiceHealth:
        """Check Azure App Configuration connection health"""
        start_time = datetime.now(timezone.utc)
        
        try:
            connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
            endpoint = os.getenv("AZURE_APP_CONFIG_ENDPOINT")
            
            if not connection_string and not endpoint:
                return ServiceHealth(
                    name="app_config",
                    status="error",
                    message="Azure App Configuration connection info not configured",
                    error="Azure App Configuration connection info not configured in environment variables. Ensure 'AZURE_APP_CONFIG_CONNECTION_STRING' or 'AZURE_APP_CONFIG_ENDPOINT' is set.",
                    last_checked=datetime.now(timezone.utc).isoformat(),
                    endpoint="Not configured"
                )
            
            # declare here to capture
            credential, token_details = None, None
            
            # Create client if not exists
            if not self.app_config_client:
                if connection_string:
                    self.app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)
                    endpoint_display = "Connection String"
                else:
                    credential, token_details = get_azure_credential_with_details()
                    self.app_config_client = AzureAppConfigurationClient(base_url=endpoint, credential=credential)
                    endpoint_display = endpoint
            else:
                endpoint_display = endpoint or "Connection String"
            
            # Try to list some configuration settings to test connectivity
            items = list(self.app_config_client.list_configuration_settings(
                key_filter="doc-proc-ui.app.*"
            ))

            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return ServiceHealth(
                name="app_config",
                status="connected",
                message="Connected successfully",
                details={
                    "config_items_count": len(items),
                    "key_prefix": "doc-proc-ui.app.*",
                    "credential_type": "connection_string" if connection_string else "default_azure_credential",
                    "credential_details": token_details if credential else None
                },
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=endpoint_display
            )
            
        except Exception as e:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="app_config",
                status="error",
                message=f"Connection failed: {e.__class__.__name__}",
                error=f'{str(e)}',
                details={"error_type": type(e).__name__},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=endpoint or connection_string or "Not configured"
            )
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check the health of a specific service"""
        if service_name == "cosmos_db":
            return await self._check_cosmos_db_health()
        elif service_name == "storage_queue":
            return await self._check_storage_queue_health()
        elif service_name == "app_config":
            return await self._check_app_config_health()
        else:
            return ServiceHealth(
                name=service_name,
                status="error",
                message=f"Unknown service: {service_name}",
                last_checked=datetime.now(timezone.utc).isoformat()
            )

# Singleton instance
health_service = HealthService()