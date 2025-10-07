"""
Startup and initialization logic for the application.
"""
import asyncio
from typing import Dict, Any
import logging

from app.dependencies import get_service_catalog_service, get_step_catalog_service, get_source_catalog_service


logger = logging.getLogger("doc-proc-ui.app.startup")


async def initialize_service_catalog():
    """Initialize service catalog on startup"""
    try:
        logger.info("Initializing service catalog...")
        service_catalog_service = get_service_catalog_service()
        
        # Load catalog services and sync to database
        result = await service_catalog_service.initialize_service_catalog()
                
        logger.info("Service catalog initialization completed successfully")
        logger.info(f"Total services in catalog: {result.get('total_catalog_services', 0)}")
        
        return {
            "status": "success",
            "added_service_count": result.get('created_count', 0),
            "service_count": result.get('total_catalog_services', 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize service catalog: {str(e)}")
        logger.exception(e)
        raise e
    
async def initialize_step_catalog():
    """Initialize step catalog on startup"""
    try:
        logger.info("Initializing step catalog...")
        step_catalog_service = get_step_catalog_service()
        
        # Load catalog services and sync to database
        result = await step_catalog_service.initialize_step_catalog()
                
        logger.info("Step catalog initialization completed successfully")
        logger.info(f"Total steps in catalog: {result.get('total_catalog_steps', 0)}")
        
        return {
            "status": "success",
            "added_step_count": result.get('created_count', 0),
            "step_count": result.get('total_catalog_steps', 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize step catalog: {str(e)}")
        logger.exception(e)
        raise e


async def initialize_source_catalog():
    """Initialize source catalog on startup"""
    try:
        logger.info("Initializing source catalog...")
        source_catalog_service = get_source_catalog_service()
        
        # Load catalog services and sync to database
        result = await source_catalog_service.initialize_source_catalog()
                
        logger.info("Source catalog initialization completed successfully")
        logger.info(f"Total source in catalog: {result.get('total_catalog_sources', 0)}")
        
        return {
            "status": "success",
            "added_source_count": result.get('created_count', 0),
            "source_count": result.get('total_catalog_sources', 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize step catalog: {str(e)}")
        logger.exception(e)
        raise e
    

async def startup_tasks():
    """Run all startup tasks"""
    logger.info("Starting application initialization tasks...")
    
    tasks = [
        initialize_service_catalog(),
        initialize_step_catalog(),
        initialize_source_catalog(),
        # Add other startup tasks here
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    has_errors = any(isinstance(result, Exception) for result in results)
    # Log results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Startup task {i} failed: {str(result)}")
        else:
            logger.info(f"Startup task {i} completed: {result}")
    
    if has_errors:
        logger.warning("⚠️ Application initialization completed with errors")
    else:
        logger.info("✅ Application initialization completed")


def create_startup_handler():
    """Create startup event handler"""
    async def startup():
        await startup_tasks()
    
    return startup


def create_shutdown_handler():
    """Create shutdown event handler"""
    async def shutdown():
        logger.info("Application is shutting down...")
        # Add cleanup tasks here if needed
        
    return shutdown
