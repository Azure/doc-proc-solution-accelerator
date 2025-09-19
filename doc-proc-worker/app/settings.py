from typing import Optional
from dotenv import load_dotenv, find_dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', 
                                      env_file_encoding='utf-8',
                                      extra='allow')

    TITLE: str = "Doc Proc Worker API"
    VERSION: str = "0.1.0"
    TIMEZONE: str = "UTC"
    DESCRIPTION: str | None = None
    DEBUG: bool = True
    DOCS_URL: str = "/docs"
    OPENAPI_URL:str = "/openapi.json"
    REDOC_URL:str = "/redoc"
    API_PREFIX:str = "/api"

    API_SERVER_HOST: str = "0.0.0.0"
    API_SERVER_PORT: int = 8010
    API_SERVER_WORKERS: int = 4
    LOG_LEVEL:str = "DEBUG"

    ALLOW_CREDENTIALS: bool = True
    ALLOW_ORIGINS: list[str] = ["*"]
    ALLOW_METHODS: list[str] = ["*"]
    ALLOW_HEADERS: list[str] = ["*"]
    
    COSMOS_DB_ENDPOINT: str
    COSMOS_DB_NAME: str = "docproc"
    COSMOS_DB_CONTAINER_PIPELINES: str = "pipelines"
    COSMOS_DB_CONTAINER_STEP_CATALOG: str = "step_catalog"
    COSMOS_DB_CONTAINER_STEP_INSTANCES: str = "step_instances"
    COSMOS_DB_CONTAINER_SERVICE_CATALOG: str = "service_catalog"
    COSMOS_DB_CONTAINER_SERVICE_INSTANCES: str = "service_instances"
    
    COSMOS_DB_CONTAINER_BATCH_EXECUTIONS: str = "batch_executions"
    COSMOS_DB_CONTAINER_PIPELINE_EXECUTIONS: str = "pipeline_executions"
    COSMOS_DB_CONTAINER_ACTIVITY_LOGS: str = "activity_logs"
    
    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Azure Storage Queue settings
    STORAGE_ACCOUNT_WORKER_QUEUE_URL: str
    STORAGE_WORKER_QUEUE_NAME: str = "docproc-execution-requests"

    
    def get_fastapi_attributes(self) -> dict[str, str | bool | None]:
        """
        Set all `FastAPI` class' attributes with the custom values.
        """
        return {
            "title": self.TITLE,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "description": self.DESCRIPTION,
            "docs_url": self.DOCS_URL,
            "openapi_url": self.OPENAPI_URL,
            "redoc_url": self.REDOC_URL,
            "api_prefix": self.API_PREFIX,
        }

@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()


load_dotenv(find_dotenv('.env'))

app_settings: AppSettings = get_settings()
