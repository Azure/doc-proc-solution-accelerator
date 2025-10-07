from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.settings import get_settings
from app.log_setup import setup_logger
from app.routers import services, health, steps, pipelines, vaults, status, sources # dashboard
from app.startup import create_startup_handler, create_shutdown_handler
from app.exceptions import add_exception_handlers

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(**settings.get_fastapi_attributes())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )
    
    # Add startup and shutdown event handlers
    app.add_event_handler("startup", create_startup_handler())
    app.add_event_handler("shutdown", create_shutdown_handler())

    
    # Include API routers
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(steps.router)
    app.include_router(sources.router)
    app.include_router(pipelines.router)
    app.include_router(vaults.router)
    app.include_router(status.router)
    # app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

    # Add custom exception handlers
    add_exception_handlers(app=app)
    
    return app


setup_logger()

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        app="main:app",
        reload=settings.DEBUG,
        #reload=False,
        host=settings.API_SERVER_HOST,
        port=settings.API_SERVER_PORT,
        workers=settings.API_SERVER_WORKERS,
        log_level=str.lower(settings.LOG_LEVEL),
        use_colors=True,
    )