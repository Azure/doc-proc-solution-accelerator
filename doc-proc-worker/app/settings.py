import os
from typing import Optional
from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from azure.appconfiguration import AzureAppConfigurationClient

from app.utils import get_azure_credential

load_dotenv()  # Load environment variables from .env file if present

AZURE_APP_CONFIG_KEY_PREFIX = "doc-proc-worker."

class AppSettings(BaseModel):
    """
    Application settings model.
    """

    # Application settings with defaults
    TITLE: str = "Doc Proc Worker"
    VERSION: str = "0.1.0"
    
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG" if DEBUG else "INFO"

    # Required settings (will be loaded from App Configuration)
    COSMOS_DB_ENDPOINT: str = ""
    COSMOS_DB_NAME: str = "docproc"
    
    # Container names in Cosmos DB
    COSMOS_DB_CONTAINER_PIPELINES: str = "pipelines"
    COSMOS_DB_CONTAINER_STEP_CATALOG: str = "step_catalog"
    COSMOS_DB_CONTAINER_STEP_INSTANCES: str = "step_instances"
    COSMOS_DB_CONTAINER_SERVICE_CATALOG: str = "service_catalog"
    COSMOS_DB_CONTAINER_SERVICE_INSTANCES: str = "service_instances"
    COSMOS_DB_CONTAINER_BATCH_EXECUTIONS: str = "batch_executions"
    COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS: str = "pipeline_executions"
    
    # Azure Storage Queue settings
    STORAGE_ACCOUNT_WORKER_QUEUE_URL: str = ""
    STORAGE_WORKER_QUEUE_NAME: str = "docproc-execution-requests"

    # Worker Pool settings
    WORKER_POOL_SIZE: int = 0  # 0 means use CPU count
    WORKER_AUTO_RESTART: bool = True
    WORKER_SHUTDOWN_TIMEOUT: int = 30  # seconds
    WORKER_HEALTH_CHECK_INTERVAL: int = 10  # seconds

    def __init__(self, **kwargs):
        """Initialize AppSettings and load configuration from Azure App Configuration"""
        super().__init__(**kwargs)
        self._load_from_app_config()

    def _load_from_app_config(self):
        """Load configuration values from Azure App Configuration"""
        try:
            # Get connection info from environment variables
            connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")
            endpoint = os.getenv("AZURE_APP_CONFIG_ENDPOINT")

            print(f"Loading configuration from Azure App Configuration with connection_string: '{connection_string}', endpoint: '{endpoint}'")

            if not connection_string and not endpoint:
                print("\033[91m🚨 DANGER: No Azure App Configuration connection string or endpoint found in environment variables\033[0m")
                raise RuntimeError("Azure App Configuration connection info not provided in environment variables.")
                
            
            # Create the client
            if connection_string:
                client = AzureAppConfigurationClient.from_connection_string(connection_string)
            else:
                credential = get_azure_credential()
                client = AzureAppConfigurationClient(base_url=endpoint, credential=credential)

            items = client.list_configuration_settings(
                key_filter=f"{AZURE_APP_CONFIG_KEY_PREFIX}*"
            )
            
            # Filter the items based on the key filter
            config_items = [item for item in items]
            print(f"Retrieved {len(config_items)} configuration items from Azure App Configuration. Only retrieved keys confirming to the prefix '{AZURE_APP_CONFIG_KEY_PREFIX}*'.")
            
            # Define the configuration keys to load
            config_keys = [
                "DEBUG",
                "COSMOS_DB_ENDPOINT",
                "COSMOS_DB_NAME",
                "COSMOS_DB_CONTAINER_PIPELINES",
                "COSMOS_DB_CONTAINER_STEP_CATALOG",
                "COSMOS_DB_CONTAINER_STEP_INSTANCES",
                "COSMOS_DB_CONTAINER_SERVICE_CATALOG",
                "COSMOS_DB_CONTAINER_SERVICE_INSTANCES",
                "COSMOS_DB_CONTAINER_BATCH_EXECUTIONS",
                "COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS",
                "STORAGE_ACCOUNT_WORKER_QUEUE_URL",
                "STORAGE_WORKER_QUEUE_NAME",
                "WORKER_POOL_SIZE",
                "WORKER_AUTO_RESTART",
                "WORKER_SHUTDOWN_TIMEOUT",
                "WORKER_HEALTH_CHECK_INTERVAL"
            ]
            
            # Load configuration values
            for key in config_keys:
                try:
                    config_setting = config_items and next((item for item in config_items if item.key == f"{AZURE_APP_CONFIG_KEY_PREFIX}{key}"), None)
                    if config_setting and config_setting.value:
                        # Convert value to appropriate type
                        value = config_setting.value
                        
                        # Handle type conversion
                        if key in ["WORKER_POOL_SIZE", "WORKER_SHUTDOWN_TIMEOUT", "WORKER_HEALTH_CHECK_INTERVAL"]:
                            value = int(value)
                        elif key in ["DEBUG", "WORKER_AUTO_RESTART"]:
                            value = value.lower() in ("true", "1", "yes", "on")
                                                
                        setattr(self, key, value)
                    
                    # try to get the value from environment variable as fallback
                    elif os.getenv(key):
                        value = os.getenv(key)
                        
                        # Handle type conversion
                        if key in ["WORKER_POOL_SIZE", "WORKER_SHUTDOWN_TIMEOUT", "WORKER_HEALTH_CHECK_INTERVAL"]:
                            value = int(value)
                        elif key in ["DEBUG", "WORKER_AUTO_RESTART"]:
                            value = value.lower() in ("true", "1", "yes", "on")
                        
                        setattr(self, key, value)
                    
                except Exception as e:
                    print(f"Could not load configuration key '{key}' from App Configuration nor from environment variables: {e}")
                    continue
                    
        except Exception as e:
            print("\033[91m🚨 DANGER: Failed to load configuration from Azure App Configuration. Application cannot start without required settings.\033[0m")
            print("\033[91mPlease ensure that the AZURE_APP_CONFIG_CONNECTION_STRING or AZURE_APP_CONFIG_ENDPOINT environment variable is set correctly and that the application has access/permissions to Azure App Configuration resource.\033[0m")
            print(f"\033[91mError details: {e}\033[0m")
            raise e
    
    def get_cosmos_db_containers(self) -> list[str]:
        """Get a list of all Cosmos DB container names used by the application"""
        return [
            self.COSMOS_DB_CONTAINER_PIPELINES,
            self.COSMOS_DB_CONTAINER_STEP_CATALOG,
            self.COSMOS_DB_CONTAINER_STEP_INSTANCES,
            self.COSMOS_DB_CONTAINER_SERVICE_CATALOG,
            self.COSMOS_DB_CONTAINER_SERVICE_INSTANCES,
            self.COSMOS_DB_CONTAINER_BATCH_EXECUTIONS,
            self.COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS
        ]

@lru_cache()
def get_settings() -> AppSettings:
    """Get cached AppSettings instance"""
    return AppSettings()

# Initialize settings
app_settings: AppSettings = get_settings()
