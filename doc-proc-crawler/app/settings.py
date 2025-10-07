import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from azure.appconfiguration import AzureAppConfigurationClient

load_dotenv()

class AppSettings(BaseModel):
    """
    Application settings model for Doc Proc Crawler.
    """

    # Application settings with defaults
    TITLE: str = "Doc Proc Crawler"
    VERSION: str = "0.1.0"
    
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG" if DEBUG else "INFO"

    # Required settings (will be loaded from App Configuration)
    COSMOS_DB_ENDPOINT: str = ""
    COSMOS_DB_NAME: str = "docproc"
    
    # Container names in Cosmos DB
    COSMOS_DB_CONTAINER_SOURCE_CATALOG: str = "source_catalog"
    COSMOS_DB_CONTAINER_SOURCE_INSTANCES: str = "source_instances"
    COSMOS_DB_CONTAINER_VAULTS: str = "vaults"
    COSMOS_DB_CONTAINER_VAULT_DOCUMENTS: str = "vault_documents"
    COSMOS_DB_CONTAINER_CRAWL_DOCUMENTS: str = "crawl_documents"
    COSMOS_DB_CONTAINER_CRAWL_EXECUTIONS: str = "crawl_executions"
    COSMOS_DB_CONTAINER_WORKER_LEASES: str = "crawl_leases"
    
    # Storage Queue settings
    STORAGE_ACCOUNT_WORKER_QUEUE_URL: str = ""
    STORAGE_WORKER_QUEUE_NAME: str = "docproc-execution-requests"
    
    # Distributed worker management settings
    CRAWLER_MAX_WORKERS: int = 3  # Maximum number of workers per machine
    CRAWLER_DISCOVERY_POLL_INTERVAL: int = 60  # How often to discover source instances (seconds)
    CRAWLER_LEASE_DURATION_MINUTES: int = 5  # Worker lease duration
    CRAWLER_LEASE_RENEWAL_INTERVAL_MINUTES: int = 3  # How often to renew leases

    def __init__(self, **kwargs):
        """Initialize AppSettings and load configuration from Azure App Configuration"""
        super().__init__(**kwargs)
        self._load_from_app_config()

    def _load_from_app_config(self):
        """Load configuration values from Azure App Configuration"""
        try:
            print(f"Loading configuration from doc proc configuration provider...")

            from app.dependencies import get_config_provider
            config_provider = get_config_provider(refresh=True)

            
            # Define the configuration keys to load
            config_keys = [
                "DEBUG",
                "COSMOS_DB_ENDPOINT",
                "COSMOS_DB_NAME",
                "COSMOS_DB_CONTAINER_SOURCE_CATALOG",
                "COSMOS_DB_CONTAINER_SOURCE_INSTANCES",
                "COSMOS_DB_CONTAINER_VAULTS",
                "COSMOS_DB_CONTAINER_DOCUMENTS",
                "COSMOS_DB_CONTAINER_VAULT_DOCUMENTS",
                "COSMOS_DB_CONTAINER_CRAWL_EXECUTIONS",
                "COSMOS_DB_CONTAINER_WORKER_LEASES",
                "CRAWLER_MAX_WORKERS",
                "CRAWLER_DISCOVERY_POLL_INTERVAL",
                "CRAWLER_LEASE_DURATION_MINUTES",
                "CRAWLER_LEASE_RENEWAL_INTERVAL_MINUTES",
                "STORAGE_ACCOUNT_WORKER_QUEUE_URL",
                "STORAGE_WORKER_QUEUE_NAME"
            ]
            
            # Load configuration values
            for key in config_keys:
                try:
                    value = config_provider.get_config_value(key)
                    
                    if value is not None:
                        # Handle type conversion
                        if key in ["CRAWLER_MAX_WORKERS",
                                 "CRAWLER_DISCOVERY_POLL_INTERVAL", "CRAWLER_LEASE_DURATION_MINUTES",
                                 "CRAWLER_LEASE_RENEWAL_INTERVAL_MINUTES"]:
                            value = int(value)
                        elif key in ["DEBUG", "WORKER_AUTO_RESTART"]:
                            value = value.lower() in ("true", "1", "yes", "on")
                                                
                        setattr(self, key, value)
                    
                except KeyError as e:
                    print(f"doc-proc-crawler.app: Configuration key '{key}' not found in Azure App Configuration nor from environment variables: {e}.")
                    print("If using App Configuration, please ensure that the key exists with correct prefix.")
                except Exception as e:
                    print(f"An error occurred while loading configuration key '{key}': {e}")
                    continue
                    
        except Exception as e:
            print("\033[91m🚨 DANGER: Failed to load configuration from Azure App Configuration. Application cannot start without required settings.\033[0m")
            print("\033[91mPlease ensure that the AZURE_APP_CONFIG_CONNECTION_STRING or AZURE_APP_CONFIG_ENDPOINT environment variable is set correctly and that the application has access/permissions to Azure App Configuration resource.\033[0m")
            print(f"\033[91mError details: {e}\033[0m")
            raise e
    
    def get_cosmos_db_containers(self) -> list[str]:
        """Get a list of all Cosmos DB container names used by the crawler application"""
        return [
            self.COSMOS_DB_CONTAINER_SOURCE_CATALOG,
            self.COSMOS_DB_CONTAINER_SOURCE_INSTANCES,
            self.COSMOS_DB_CONTAINER_VAULTS,
            self.COSMOS_DB_CONTAINER_VAULT_DOCUMENTS,
            self.COSMOS_DB_CONTAINER_CRAWL_DOCUMENTS,
            self.COSMOS_DB_CONTAINER_CRAWL_EXECUTIONS,
            self.COSMOS_DB_CONTAINER_WORKER_LEASES
        ]

@lru_cache()
def get_settings() -> AppSettings:
    """Get cached AppSettings instance"""
    return AppSettings()

# Initialize settings
app_settings: AppSettings = get_settings()
