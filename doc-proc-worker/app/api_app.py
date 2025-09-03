from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import pipelines, services, steps, executions
from app.settings import app_settings


def create_app() -> FastAPI:
    app = FastAPI(**app_settings.get_fastapi_attributes())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.ALLOW_ORIGINS,
        allow_credentials=app_settings.ALLOW_CREDENTIALS,
        allow_methods=app_settings.ALLOW_METHODS,
        allow_headers=app_settings.ALLOW_HEADERS,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(services.router, prefix="/api/services", tags=["services"])
    app.include_router(steps.router, prefix="/api/steps", tags=["steps"])
    app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"])
    app.include_router(executions.router, prefix="/api/executions", tags=["executions"])

    return app


app: FastAPI = create_app()

# if __name__ == "__main__":
#     uvicorn.run(
#         app=app,
#         reload=app_settings.DEBUG,
#         host=app_settings.API_SERVER_HOST,
#         port=app_settings.API_SERVER_PORT,
#         workers=app_settings.API_SERVER_WORKERS,
#         #log_level=str.lower(app_settings.LOG_LEVEL),
#         use_colors=True,
#     )