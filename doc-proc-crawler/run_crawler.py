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

from utils.startup import load_source_catalog_config,  load_crawler_config, load_crawler

from configuration import Configuration
from dependencies import get_config
from telemetry import Telemetry
from constants import APPLICATION_INSIGHTS_CONNECTION_STRING, APP_NAME
from utils.tools import is_azure_environment
from connectors import CosmosDBClient

from app.crawler.crawler_config import CrawlerConfig
from app.crawler.crawler_base import Crawler

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

logger = logging.getLogger("doc.proc.crawler")
      
@asynccontextmanager
async def lifespan(app: FastAPI):

    #Telemetry.configure_monitoring(config, APPLICATION_INSIGHTS_CONNECTION_STRING, APP_NAME)
    Telemetry.setup_logging(logger)

    # Start the scheduler    
    scheduler.start()

    # Load source catalog configuration
    source_catalog_yaml_file = 'source_catalog.yaml'
    source_catalog_config = await load_source_catalog_config(source_catalog_yaml_file)

    # Load crawler configuration
    crawler_config_yaml_file = 'crawler_config.yaml'
    crawler_configs = await load_crawler_config(crawler_config_yaml_file=crawler_config_yaml_file, 
                                                 source_catalog_config=source_catalog_config)

    # load the crawler jobs
    crawler_config : CrawlerConfig
    for crawler_config in crawler_configs:
        try:
            crawler = await load_crawler(crawler_config=crawler_config, 
                                           source_catalog_config=source_catalog_config)
        except Exception as e:
            logging.error(f"Error loading crawler '{crawler_config.name}': {e}")
            continue

        try:
            trigger = CronTrigger.from_crontab(crawler_config.crawl_schedule)
            scheduler.add_job(
                crawler.crawl,
                trigger=trigger,
                id=f"crawler_{crawler.name}_crawl",
                replace_existing=True,
            )
            logging.info(f"Scheduled {crawler.name} @ {crawler_config.crawl_schedule}")
        except ValueError:
            logging.error(f"Invalid CRON expression for crawler '{crawler.name}': {crawler_config.crawl_schedule!r}")

        try:
            trigger = CronTrigger.from_crontab(crawler_config.purge_schedule)
            scheduler.add_job(
                crawler.purge,
                trigger=trigger,
                id=f"crawler_{crawler.name}_purge",
                replace_existing=True,
            )
            logging.info(f"Scheduled {crawler.name} @ {crawler_config.purge_schedule}")
        except ValueError:
            logging.error(f"Invalid CRON expression for crawler '{crawler.name}': {crawler_config.purge_schedule!r}")

    yield

    scheduler.shutdown(wait=False)

app = FastAPI(lifespan=lifespan)

FastAPIInstrumentor.instrument_app(app)
#HTTPXClientInstrumentor.instrument()

if (not is_azure_environment()):
    # Run the app locally
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug", timeout_keep_alive=60)
    