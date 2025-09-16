import asyncio
from typing import List
from colorama import Fore, Style, init
from dotenv import load_dotenv
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import uvicorn

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_base import StepInputOutput
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.source_config import SourceConfig

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

init(autoreset=True)

load_dotenv()

logger = logging.getLogger("doc.proc")

def setup_logging(logger: logging.Logger):
    """Setup logging configuration."""
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    class ColorFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT,
        }
        def format(self, record):
            color = self.COLORS.get(record.levelno, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"

    formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

async def load_source_catalog_config(source_catalog_yaml_file: str) -> SourceConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_source_catalog_config_from_file(source_catalog_yaml_file)
    elif source == "cosmos":
        return await load_source_catalog_config_from_cosmos(source_catalog_yaml_file)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_source_catalog_config_from_cosmos(document_id: str) -> SourceConfig:

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id)

    try:
        # Load source configuration
        source_catalog = SourceConfig.from_dict(document)
        logger.info(f"Source configuration loaded successfully.")
        logger.debug(f"Source configuration: {source_catalog}")

        return source_catalog
        
    except Exception as e:
        logger.error(f"Error loading source catalog: {e}")

async def load_source_catalog_config_from_file(source_catalog_yaml_file: str) -> SourceConfig:

    # Example usage of SourceConfig
    yaml_str = ''

    with open(source_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load source configuration
        source_catalog = SourceConfig.from_yaml(yaml_str)
        logger.info(f"Source configuration loaded successfully.")
        logger.debug(f"Source configuration: {source_catalog}")

        return source_catalog

    except Exception as e:
        logger.error(f"Error loading source catalog: {e}")

async def load_services_catalog_config(services_catalog_yaml_file: str) -> ServiceConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_services_catalog_config_from_file(services_catalog_yaml_file)
    elif source == "cosmos":
        return await load_services_catalog_config_from_cosmos(services_catalog_yaml_file)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_services_catalog_config_from_cosmos(document_id: str) -> ServiceConfig:

    container_name = config.get("DOCPROC_CONTAINER_NAME", "docproc")
    document = cosmos.get_document(container_name, document_id)

    try:
        # Load services configuration
        service_catalog = ServiceConfig.from_dict(document)
        logger.info(f"Service configuration loaded successfully.")
        logger.debug(f"Service configuration: {service_catalog}")
        
        return service_catalog
        
    except Exception as e:
        logger.error(f"Error loading service catalog: {e}")

async def load_services_catalog_config_from_file(services_catalog_yaml_file: str) -> ServiceConfig:

    # Example usage of ServiceConfig
    yaml_str = ''

    with open(services_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load services configuration
        service_catalog = ServiceConfig.from_yaml(yaml_str)
        logger.info(f"Service configuration loaded successfully.")
        logger.debug(f"Service configuration: {service_catalog}")
        
        return service_catalog
        
    except Exception as e:
        logger.error(f"Error loading service catalog: {e}")

async def load_step_catalog_config(step_catalog_yaml_file: str) -> StepConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_step_catalog_config_from_file(step_catalog_yaml_file)
    elif source == "cosmos":
        return await load_step_catalog_config_from_cosmos(step_catalog_yaml_file)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_step_catalog_config_from_cosmos(document_id: str) -> StepConfig:

    container_name = config.get("step_catalog_source_container", "doc-proc")
    document = cosmos.get_document(container_name, document_id)

    try:
        # Load steps configuration
        step_catalog = StepConfig.from_dict(document)
        logger.info(f"Step configuration loaded successfully.")
        logger.debug(f"Step configuration: {step_catalog}")

        return step_catalog

    except Exception as e:
        logger.error(f"Error loading step catalog: {e}")

async def load_step_catalog_config_from_file(step_catalog_yaml_file: str) -> StepConfig:

    # Example usage of ServiceConfig
    yaml_str = ''

    with open(step_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load steps configuration
        step_catalog = StepConfig.from_yaml(yaml_str)
        logger.info(f"Step configuration loaded successfully.")
        logger.debug(f"Step configuration: {step_catalog}")

        return step_catalog

    except Exception as e:
        logger.error(f"Error loading step catalog: {e}")

async def load_pipeline_config(pipeline_config_yaml_file: str, 
                               step_catalog_config: List[StepConfig] = None, 
                               service_catalog_config: List[ServiceConfig] = None, 
                               source_catalog_config: List[SourceConfig] = None) -> PipelineConfig:
    source = config.get("CATALOG_SOURCE", "file")
    if source == "file":
        return await load_pipeline_config_from_file(pipeline_config_yaml_file, step_catalog_config, service_catalog_config, source_catalog_config)
    elif source == "cosmos":
        return await load_pipeline_config_from_cosmos(pipeline_config_yaml_file, step_catalog_config, service_catalog_config, source_catalog_config)
    else:
        raise ValueError(f"Unknown services catalog source: {source}")

async def load_pipeline_config_from_cosmos(document_id: str, step_catalog_config: List[StepConfig] = None, service_catalog_config: List[ServiceConfig] = None, source_catalog_config: List[SourceConfig] = None) -> PipelineConfig:
    """Load pipeline configuration from a YAML file."""

    container_name = config.get("pipeline_catalog_source_container", "doc-proc")
    document = cosmos.get_document(container_name, document_id)

    try:
        # Load pipeline configuration
        pipeline_config = PipelineConfig.from_dict(document, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)
        logger.info(f"Pipeline configuration loaded successfully.")
        logger.debug(f"Pipeline configuration: {pipeline_config}")

        return pipeline_config

    except Exception as e:
        logger.error(f"Error loading pipeline configuration: {e}")


async def load_pipeline_config_from_file(pipeline_config_yaml_file: str, 
                                         step_catalog_config: List[StepConfig] = None, 
                                         service_catalog_config: List[ServiceConfig] = None,
                                         source_catalog_config: List[SourceConfig] = None) -> PipelineConfig:
    """Load pipeline configuration from a YAML file."""
    
    yaml_str = ''

    with open(pipeline_config_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load pipeline configuration
        pipeline_config = PipelineConfig.from_yaml(yaml_str, 
                                                   step_catalog_config=step_catalog_config, 
                                                   service_catalog_config=service_catalog_config,
                                                   source_catalog_config=source_catalog_config)
        logger.info(f"Pipeline configuration loaded successfully.")
        logger.debug(f"Pipeline configuration: {pipeline_config}")

        return pipeline_config

    except Exception as e:
        logger.error(f"Error loading pipeline configuration: {e}")


async def load_pipeline(pipeline_config: PipelineConfig, 
                        step_catalog_config: List[StepConfig] = None, 
                        service_catalog_config: List[ServiceConfig] = None, 
                        source_catalog_config: List[SourceConfig] = None) -> "Pipeline":
    """Load pipeline from configuration."""
    
    if not pipeline_config:
        raise ValueError("Pipeline configuration cannot be None or empty.")

    if not isinstance(pipeline_config, PipelineConfig):
        raise TypeError(f"Expected PipelineConfig instance, got {type(pipeline_config)}")

    # Create the pipeline instance
    pipeline = await Pipeline.create(pipeline_config=pipeline_config,
                                     step_catalog_config=step_catalog_config,
                                     service_catalog_config=service_catalog_config,
                                     source_catalog_config=source_catalog_config
                                    )

    logger.info(f"Pipeline '{pipeline.name}' loaded successfully with {len(pipeline.pipeline_execution_steps)} execution steps.")
    
    return pipeline


#####
#####
##### Main function to load and execute the pipeline
#####
async def main():

    # Load services catalog configuration
    services_catalog_yaml_file = 'service_catalog.yaml'
    service_catalog_config = await load_services_catalog_config(services_catalog_yaml_file)


    # Load steps catalog configuration
    step_catalog_yaml_file = 'step_catalog.yaml'
    step_catalog_config = await load_step_catalog_config(step_catalog_yaml_file)


    # Load pipeline configuration
    pipeline_config_yaml_file = 'pipeline_config.yaml'
    pipeline_config = await load_pipeline_config(pipeline_config_yaml_file=pipeline_config_yaml_file, 
                                                 step_catalog_config=step_catalog_config, 
                                                 service_catalog_config=service_catalog_config)


    # get the configuration for the first pipeline
    first_pipeline = pipeline_config[0] if pipeline_config else None

    # Load the pipeline
    try:
        pipeline = await load_pipeline(pipeline_config=first_pipeline, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)

        # Run the pipeline
        input_data = StepInputOutput(summary_data={}, data={ "documents": generate_documents() })
        
        result = await pipeline.run(input_data=input_data)
        
        logger.info(f"Pipeline '{pipeline.name}' executed successfully.")
        logger.info(f"Pipeline result: {result}")

    except Exception as e:
        logger.error(f"Error executing pipeline: {e}.")
        logger.error("Pipeline execution failed. Please check the logs for more details.")

      
def generate_documents():
    """Generate a list of documents to process."""
    # This is a placeholder function. In a real application, this would fetch documents from a source.
    return [
            {"file_path": "/Users/nadeemis/temp/Lorem Ipsum Sample Document.pdf"},
            {"file_path": "/Users/nadeemis/temp/Lorem Ipsum Presentation.pptx"},
            {"file_path": "/Users/nadeemis/temp/Lorem Ipsum Sample Document.docx"}
        ]

@asynccontextmanager
async def lifespan(app: FastAPI):

    #Telemetry.configure_monitoring(config, APPLICATION_INSIGHTS_CONNECTION_STRING, APP_NAME)
    setup_logging(logger)

    # Inicia o scheduler antes de agendar qualquer tarefa
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

if (not is_azure_environment()):
    # Run the app locally
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="debug", timeout_keep_alive=60)
    