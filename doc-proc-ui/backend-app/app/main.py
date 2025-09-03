from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import pipelines, services, steps, executions
from .config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Doc Proc Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(services.router, prefix="/api/services", tags=["services"])
    app.include_router(steps.router, prefix="/api/steps", tags=["steps"])
    app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"])
    app.include_router(executions.router, prefix="/api/executions", tags=["executions"])

    return app


app = create_app()
