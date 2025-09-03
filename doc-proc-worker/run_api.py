#!/usr/bin/env python3
"""
Celery worker entry point for document processing pipeline execution.

Usage:
    python run_api.py

"""

import os
import sys
import uvicorn

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# from app.api_app import app
from app.settings import app_settings

if __name__ == "__main__":
    uvicorn.run(
        app="app.api_app:app",
        reload=app_settings.DEBUG,
        host=app_settings.API_SERVER_HOST,
        port=app_settings.API_SERVER_PORT,
        workers=app_settings.API_SERVER_WORKERS,
        #log_level=str.lower(app_settings.LOG_LEVEL),
        use_colors=True,
    )