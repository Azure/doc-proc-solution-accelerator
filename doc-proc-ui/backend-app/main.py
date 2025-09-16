from functools import lru_cache

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.settings import app_settings
from app.logging import setup_logger
from app.routers import services, health, steps, pipelines #, executions, vaults, dashboard
from app.startup import create_startup_handler, create_shutdown_handler
from app.exceptions import add_exception_handlers

def create_app() -> FastAPI:
    app = FastAPI(**app_settings.get_fastapi_attributes())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.ALLOW_ORIGINS,
        allow_credentials=app_settings.ALLOW_CREDENTIALS,
        allow_methods=app_settings.ALLOW_METHODS,
        allow_headers=app_settings.ALLOW_HEADERS,
    )
    
    # Add startup and shutdown event handlers
    app.add_event_handler("startup", create_startup_handler())
    app.add_event_handler("shutdown", create_shutdown_handler())

    
    # Include API routers
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(steps.router)
    app.include_router(pipelines.router)
    # app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
    # app.include_router(vaults.router, prefix="/api/vaults", tags=["vaults"])
    # app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

    # Add custom exception handlers
    add_exception_handlers(app=app)
    
    return app


setup_logger()

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        reload=app_settings.DEBUG,
        host=app_settings.API_SERVER_HOST,
        port=app_settings.API_SERVER_PORT,
        workers=app_settings.API_SERVER_WORKERS,
        log_level=str.lower(app_settings.LOG_LEVEL),
        use_colors=True,
    )