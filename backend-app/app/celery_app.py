import os
from celery import Celery
from kombu import Queue

# Create Celery app
celery_app = Celery("doc_proc_backend")

# Configuration
celery_app.conf.update(
    # Broker settings
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Queue configuration
    task_routes={
        "doc_proc_backend.tasks.execute_pipeline_batch": {"queue": "pipeline_execution"},
        "doc_proc_backend.tasks.process_single_document": {"queue": "document_processing"},
    },
    
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("pipeline_execution", routing_key="pipeline_execution"),
        Queue("document_processing", routing_key="document_processing"),
    ),
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
)

# Import tasks to register them
from .tasks import execute_pipeline_batch, process_single_document

if __name__ == "__main__":
    celery_app.start()
