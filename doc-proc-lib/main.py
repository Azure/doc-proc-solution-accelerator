import asyncio
import uvicorn
import logging

from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from doc.proc.step.step_base import StepInputOutput
from utils.startup import load_services_catalog_config, load_source_catalog_config, load_step_catalog_config , load_pipeline_config, load_pipeline

from configuration import Configuration
from dependencies import get_config, validate_api_key_header
from telemetry import Telemetry
from constants import APPLICATION_INSIGHTS_CONNECTION_STRING, APP_NAME
from utils.tools import is_azure_environment
from connectors import CosmosDBClient

# -------------------------------
# Load App Configuration into ENV
# -------------------------------
config : Configuration = get_config()
cosmos = CosmosDBClient(config)

# -------------------------------
# FastAPI app + Scheduler
# -------------------------------
scheduler = AsyncIOScheduler(timezone="UTC")

load_dotenv()

logger = logging.getLogger("doc.proc")
      
@asynccontextmanager
async def lifespan(app: FastAPI):

    #Telemetry.configure_monitoring(config, APPLICATION_INSIGHTS_CONNECTION_STRING, APP_NAME)
    Telemetry.setup_logging(logger)

    # Start the scheduler    
    scheduler.start()

    # Load services catalog configuration
    services_catalog_yaml_file = 'service_catalog.yaml'
    service_catalog_config = await load_services_catalog_config(services_catalog_yaml_file)


    # Load source catalog configuration
    source_catalog_yaml_file = 'source_catalog.yaml'
    source_catalog_config = await load_source_catalog_config(source_catalog_yaml_file)

    # Load steps catalog configuration
    step_catalog_yaml_file = 'step_catalog.yaml'
    step_catalog_config = await load_step_catalog_config(step_catalog_yaml_file)

    # Load pipeline configuration
    pipeline_config_yaml_file = 'pipeline_config.yaml'
    pipeline_configs = await load_pipeline_config(pipeline_config_yaml_file=pipeline_config_yaml_file, 
                                                 step_catalog_config=step_catalog_config, 
                                                 service_catalog_config=service_catalog_config,
                                                 source_catalog_config=source_catalog_config)

    # load the pipeline jobs
    for pipeline_config in pipeline_configs:
        try:
            pipeline = await load_pipeline(pipeline_config=pipeline_config, 
                                           step_catalog_config=step_catalog_config, 
                                           service_catalog_config=service_catalog_config,
                                           source_catalog_config=source_catalog_config)
        except Exception as e:
            logging.error(f"Error loading pipeline '{pipeline_config.name}': {e}")
            continue

        cron_expr = pipeline_config.schedule
        try:
            trigger = CronTrigger.from_crontab(cron_expr)
            scheduler.add_job(
                pipeline.run,
                trigger=trigger,
                id=f"pipeline_{pipeline.name}",
                replace_existing=True,
            )
            logging.info(f"Scheduled {pipeline.name} @ {cron_expr}")
        except ValueError:
            logging.error(f"Invalid CRON expression for pipeline '{pipeline.name}': {cron_expr!r}")

    yield

    scheduler.shutdown(wait=False)

app = FastAPI(lifespan=lifespan)

FastAPIInstrumentor.instrument_app(app)
#HTTPXClientInstrumentor.instrument()

if (not is_azure_environment()):
    # Run the app locally
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="debug", timeout_keep_alive=60)
    