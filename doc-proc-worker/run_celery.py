#!/usr/bin/env python3
"""
Celery worker entry point for document processing pipeline execution.

Usage:
    python run_celery.py worker --loglevel=info --concurrency=4

Or using celery directly:
    celery -A app.celery_app worker --loglevel=info --concurrency=4
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logging import setup_logger
from app.celery_app import celery_app

# Import tasks to register them
from app.tasks import execute_pipeline_batch, process_single_document

if __name__ == "__main__":
    setup_logger()
    
    args = ['worker', '--loglevel=DEBUG']
    celery_app.start(argv=args)
