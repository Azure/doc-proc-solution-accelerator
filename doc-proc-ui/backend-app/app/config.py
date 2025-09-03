import os
from functools import lru_cache
from typing import List


class Settings:
    cosmos_endpoint: str
    cosmos_key: str
    cosmos_db_name: str = "docproc"
    container_services: str = "services"
    container_steps: str = "steps"
    container_pipelines: str = "pipelines"
    container_batch_executions: str = "batch_executions"
    container_activities: str = "activities"
    container_step_outputs: str = "step_outputs"
    allow_origins: List[str]
    
    # Celery settings
    celery_broker_url: str
    celery_result_backend: str

    def __init__(self) -> None:
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT") or os.getenv("COSMOS_URI", "").strip()
        self.cosmos_key = os.getenv("COSMOS_KEY", "").strip()
        self.cosmos_db_name = os.getenv("COSMOS_DB_NAME", self.cosmos_db_name)
        self.container_services = os.getenv("COSMOS_CONTAINER_SERVICES", self.container_services)
        self.container_steps = os.getenv("COSMOS_CONTAINER_STEPS", self.container_steps)
        self.container_pipelines = os.getenv("COSMOS_CONTAINER_PIPELINES", self.container_pipelines)
        self.container_batch_executions = os.getenv("COSMOS_CONTAINER_BATCH_EXECUTIONS", self.container_batch_executions)
        self.container_activities = os.getenv("COSMOS_CONTAINER_ACTIVITIES", self.container_activities)
        self.container_step_outputs = os.getenv("COSMOS_CONTAINER_STEP_OUTPUTS", self.container_step_outputs)
        allow = os.getenv("ALLOW_ORIGINS", "*")
        self.allow_origins = [o.strip() for o in allow.split(",") if o.strip()]
        
        # Celery configuration
        self.celery_broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        self.celery_result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
