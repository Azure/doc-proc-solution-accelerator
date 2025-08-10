#!/usr/bin/env python3
"""
Celery worker entry point for document processing pipeline execution.

Usage:
    python celery_worker.py worker --loglevel=info --concurrency=4

Or using celery directly:
    celery -A app.celery_app worker --loglevel=info --concurrency=4
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()
