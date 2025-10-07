"""
Health service for checking the status of various system components.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel

from azure.cosmos import CosmosClient
from azure.storage.queue import QueueServiceClient
from azure.appconfiguration import AzureAppConfigurationClient
from azure.core.exceptions import ServiceRequestError, ResourceNotFoundError

from doc.proc.providers.credential_provider import get_azure_credential_with_details

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

    def __init__(self, 
                 cosmos_endpoint: str = None, 
                 cosmos_db_name: str = None,
                 cosmos_db_containers: List[str] = None,
                 blob_storage_account: str = None,
                 blob_storage_container: str = None,
                 storage_account_worker_queue_url: str = None,
                 storage_worker_queue_name: str = None):
        
        self.cosmos_endpoint = cosmos_endpoint
        self.cosmos_db_name = cosmos_db_name
        self.cosmos_db_containers = cosmos_db_containers
        self.blob_storage_account = blob_storage_account
        self.blob_storage_container = blob_storage_container
        self.storage_account_worker_queue_url = storage_account_worker_queue_url
        self.storage_worker_queue_name = storage_worker_queue_name
        
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
            self._check_blob_storage_health(),
            self._check_storage_queue_health(),
            return_exceptions=True
        )
        
        service_names = ["app_config", "cosmos_db", "blob_storage", "storage_queue"]
        
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
            logger.debug(f"Checking Cosmos DB health with endpoint: {self.cosmos_endpoint}")

            if not self.cosmos_endpoint:
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
                    url=self.cosmos_endpoint,
                    credential=credential
                )
            
            # Try to get database info
            database = self.cosmos_client.get_database_client(self.cosmos_db_name)
            
            # Simple read operation to test connectivity
            database_properties = database.read()

            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return ServiceHealth(
                name="cosmos_db",
                status="connected",
                message="Connected successfully",
                details={
                    "database_name": self.cosmos_db_name,
                    "database_id": database_properties.get("id"),
                    "container_count": len(self.cosmos_db_containers) if self.cosmos_db_containers else 0,
                    "credential_type": "default_azure_credential",
                    "credential_details": token_details
                },
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=self.cosmos_endpoint
            )
            
        except ResourceNotFoundError:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="cosmos_db",
                status="error",
                message="Database not found",
                error=f"Database '{self.cosmos_db_name}' not found",
                details={"error_type": "ResourceNotFoundError"},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=self.cosmos_endpoint
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
                endpoint=self.cosmos_endpoint
            )
    
    
    async def _check_blob_storage_health(self) -> ServiceHealth:
        """Check Azure Blob Storage connection health"""
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.debug(f"Checking blob storage health with account: {self.blob_storage_account} and container: {self.blob_storage_container}")

            if not self.blob_storage_account or not self.blob_storage_container:
                return ServiceHealth(
                    name="blob_storage",
                    status="error",
                    message="Blob Storage account details not configured",
                    error="Blob Storage account details not configured in Azure App Configuration. Ensure 'BLOB_STORAGE_ACCOUNT_NAME' and 'BLOB_STORAGE_CONTAINER_NAME' are set using the correct key prefix.",
                    last_checked=datetime.now(timezone.utc).isoformat(),
                    endpoint="Not configured"
                )
            
            credential, token_details = get_azure_credential_with_details()
            from azure.storage.blob import BlobServiceClient
            
            # Create client
            account_url = f"https://{self.blob_storage_account}.blob.core.windows.net"
            blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
            
            # Try to get container properties
            container_client = blob_service_client.get_container_client(self.blob_storage_container)
            properties = container_client.get_container_properties()

            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return ServiceHealth(
                name="blob_storage",
                status="connected",
                message="Connected successfully",
                details={
                    "container_name": self.blob_storage_container,
                    "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
                    "lease_status": properties.lease.status if properties.lease else None,
                    "credential_type": "default_azure_credential",
                    "credential_details": token_details
                },
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=f"{account_url}/{self.blob_storage_container}"
            )
            
        except ResourceNotFoundError:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="blob_storage",
                status="error",
                message=f"Container '{self.blob_storage_container}' not found",
                error=f"Container '{self.blob_storage_container}' not found",
                details={"error_type": "ResourceNotFoundError"},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=f"https://{self.blob_storage_account}.blob.core.windows.net"
            )
        except Exception as e:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="blob_storage",
                status="error",
                message=f"Connection failed: {e.__class__.__name__}",
                error=f'{str(e)}',
                details={"error_type": type(e).__name__},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=f"https://{self.blob_storage_account}.blob.core.windows.net"
            )
    
    async def _check_storage_queue_health(self) -> ServiceHealth:
        """Check Azure Storage Queue connection health"""
        start_time = datetime.now(timezone.utc)
        
        try:

            logger.debug(f"Checking storage queue health with URL: {self.storage_account_worker_queue_url} and queue name: {self.storage_worker_queue_name}")

            if not self.storage_account_worker_queue_url:
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
                account_url = self.storage_account_worker_queue_url
                
                self.queue_client = QueueServiceClient(
                    account_url=account_url,
                    credential=credential
                )
            
            # Try to get queue properties
            queue_client = self.queue_client.get_queue_client(self.storage_worker_queue_name)
            properties = queue_client.get_queue_properties()

            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return ServiceHealth(
                name="storage_queue",
                status="connected",
                message="Connected successfully",
                details={
                    "queue_name": self.storage_worker_queue_name,
                    "approximate_message_count": properties.approximate_message_count,
                    "metadata": properties.metadata,
                    "credential_type": "default_azure_credential",
                    "credential_details": token_details
                },
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=self.storage_account_worker_queue_url
            )
            
        except ResourceNotFoundError:
            response_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            return ServiceHealth(
                name="storage_queue",
                status="error",
                message=f"Queue '{self.storage_worker_queue_name}' not found",
                error=f"Queue '{self.storage_worker_queue_name}' not found",
                details={"error_type": "ResourceNotFoundError"},
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc).isoformat(),
                endpoint=self.storage_account_worker_queue_url
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
                endpoint=self.storage_account_worker_queue_url
            )
    
    async def _check_app_config_health(self) -> ServiceHealth:
        """Check Azure App Configuration connection health"""
        start_time = datetime.now(timezone.utc)
        
        try:
            connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
            endpoint = os.getenv("AZURE_APP_CONFIG_ENDPOINT")
            
            logger.debug(f"Checking App Configuration health with connection string: {connection_string} and endpoint: {endpoint}")
            
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
        elif service_name == "blob_storage":
            return await self._check_blob_storage_health()
        else:
            return ServiceHealth(
                name=service_name,
                status="error",
                message=f"Unknown service: {service_name}",
                last_checked=datetime.now(timezone.utc).isoformat()
            )
