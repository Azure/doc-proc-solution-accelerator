import asyncio
import logging
import threading
import time
import uvicorn
import json
import multiprocessing
import concurrent.futures

from typing import List

from multiprocessing.pool import ThreadPool
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from configuration import Configuration
from dependencies import get_config, validate_api_key_header
from telemetry import Telemetry
from constants import APPLICATION_INSIGHTS_CONNECTION_STRING, APP_NAME
from utils.tools import is_azure_environment
from connectors import CosmosDBClient

from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_processing_type import DocProcProcessingType
from doc.proc.models.docproc_step import DocProcStep
from doc.proc.pipeline.pipeline_base import Pipeline, PipelineExecutionContext
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_base import ServiceBase
from doc.proc.source.source_base import SourceBase
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.source_config import SourceConfig
from doc.proc.state.docproc_state_service import DocProcStateService
from doc.proc.models.docproc_state import DocProcState
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.step.step_base import StepInputOutput, StepInstanceConfig, StepExecutionError
from doc.proc.threads.async_thread_pool import AsyncThreadPool

from factory.step_factory import StepFactory

from utils.startup import load_services_catalog_config, load_source_catalog_config, load_step_catalog_config , load_pipeline_config, load_pipeline

# -------------------------------
# Load App Configuration into ENV
# -------------------------------
config : Configuration = get_config()
cosmos = CosmosDBClient(config)

from connectors import BlobQueueClient
queue_client = BlobQueueClient()

# -------------------------------
# FastAPI app + Scheduler
# -------------------------------
scheduler = AsyncIOScheduler(timezone="UTC")

logger = logging.getLogger("doc.proc.worker")

max_messages = int(config.get("QUEUE_MAX_MESSAGES", 5))
visibility_timeout = int(config.get("QUEUE_VISIBILITY_TIMEOUT", 30))
wait_time = int(config.get("QUEUE_WAIT_TIME", 5))
max_threads = int(config.get("WORKER_MAX_THREADS", 5))

Telemetry.setup_logging(logger)

worker = None

class Worker:

    pipelines: List[Pipeline] = []
    service_catalog_config: ServiceConfig
    source_catalog_config: SourceConfig
    step_catalog_config: StepConfig

    pool : AsyncThreadPool

    async def create() -> "Worker":

        worker = Worker()

        #worker.pool = ThreadPool(processes=max_threads)
        worker.pool = AsyncThreadPool()

        # Load services catalog configuration
        services_catalog_yaml_file = 'service_catalog.yaml'
        worker.service_catalog_config = await load_services_catalog_config(services_catalog_yaml_file)

        # Load source catalog configuration
        source_catalog_yaml_file = 'source_catalog.yaml'
        worker.source_catalog_config = await load_source_catalog_config(source_catalog_yaml_file)

        # Load steps catalog configuration
        step_catalog_yaml_file = 'step_catalog.yaml'
        worker.step_catalog_config = await load_step_catalog_config(step_catalog_yaml_file)

        # Load pipeline configuration
        pipeline_config_yaml_file = 'pipeline_config.yaml'
        worker.pipeline_configs = await load_pipeline_config(pipeline_config_yaml_file=pipeline_config_yaml_file, 
                                                    step_catalog_config=worker.step_catalog_config, 
                                                    service_catalog_config=worker.service_catalog_config,
                                                    source_catalog_config=worker.source_catalog_config)
        
        #create the pipeline
        for pipeline_config in worker.pipeline_configs:
            worker.pipelines.append(await Pipeline.create(pipeline_config, 
                                                        worker.step_catalog_config,
                                                        worker.service_catalog_config,
                                                        worker.source_catalog_config                                                        
                                                        ))

        return worker

    async def run(self):
        messages = await queue_client.receive_messages(max_messages=max_messages, visibility_timeout=visibility_timeout, wait_time=wait_time)
        
        for message in messages:
            await self.run_thread(message)

        #self.execute_messages(messages)

    def thread_callback(self, args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = loop.run_until_complete(self.run_thread(args))
        loop.close()
        return future
    
    def execute_messages(self, messages):
        with concurrent.futures.ThreadPoolExecutor(max_workers = max_threads) as executor:
            futures = {executor.submit(self.thread_callback, message): message for message in messages}
            for future in concurrent.futures.as_completed(futures):
                try:
                    data = future.result()
                except Exception as exc:
                    print(exc)
        
    async def run_thread(self, message):
        try:
            await self.process_message(message)
            await queue_client.delete_message(message)
            return True
        except StepExecutionError as ex:
            logging.error(ex)
            if ex.cancel_request:
                await queue_client.delete_message(message)
        except Exception as ex:
            logging.error(ex)

        return False

    async def process_message(self, message):
        content = json.loads(message.content)
        start = content.get('execution_start', datetime.now(timezone.utc))
        end = content.get('execution_end', datetime.now(timezone.utc))
        if start == None:
            start = datetime.now(timezone.utc)
        if end == None:
            end = datetime.now(timezone.utc)
        content['execution_start'] = start
        content['execution_end'] = end
        await self.process_request(DocProcRequest(**content))

    async def process_request(self, request : DocProcRequest):

        for pipeline in self.pipelines:
            if pipeline.name == request.pipeline_name:
                context = PipelineExecutionContext(pipeline=pipeline, services=pipeline.services, sources=pipeline.sources, start_time=datetime.now())
                break

        if (await pipeline.docproc_state_service.has_state(request)):
            state = await pipeline.docproc_state_service.get_state(request)
        else:
            state = DocProcState(
                content_identifier = request.content_identifier,
                pipeline_name = request.pipeline_name,
                pipeline_object_id = request.pipeline_object_id,
                request = request
            )

        for step in request.steps:

            if step.id in state.request.completed_steps:
                continue

            try:
                input_data = await self.process_step(step, context, request, state)

                state.request.completed_steps.append(step.id)
                state.request.current_step = step.id
                state.request.last_successful_step_time = datetime.now(timezone.utc)
                await pipeline.docproc_state_service.save_state(state)

            except StepExecutionError as error:
                state.request.error_count += 1
                error.error_count = state.request.error_count
                await pipeline.docproc_state_service.save_state(state)
                raise error

    async def process_step(self, step : DocProcStep, context: PipelineExecutionContext, request: DocProcRequest, state: DocProcState):

        for step_instance in context.pipeline.pipeline_execution_steps:
            if step_instance.name == step.id:
                break

        try:
            input_data = StepInputOutput(data={"documents": [state.content_identifier.metadata]})

            # Evaluate condition if present
            if step_instance.condition:
                if not step_instance.evaluate_document_condition(state.content_identifier.metadata, input_data):
                    return input_data
                
            input_data = await step_instance.run(input_data=input_data, context=context, request=request, state=state)
        except StepExecutionError as e:
            logging.error(e)
            state.add_log_entry(step_instance, request.pipeline_execution_id, request.pipeline_execution_id, str(e))
            raise

        return input_data

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Inicia o scheduler antes de agendar qualquer tarefa
    scheduler.start()

    worker = await Worker.create()

    #run every two mins
    cron_expr = "*/2 * * * *"
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(
        worker.run,
        trigger=trigger,
        id=f"pipeline_worker",
        replace_existing=True,
    )
    
    yield

    scheduler.shutdown(wait=False)

app = FastAPI(lifespan=lifespan)

FastAPIInstrumentor.instrument_app(app)
#HTTPXClientInstrumentor.instrument()

@app.post("/process-request", dependencies=[Depends(validate_api_key_header)])
async def http_process_request(request: DocProcRequest):
    
    start_time = time.time()

    try:

        if (request.processing_type == DocProcProcessingType.asynchronous.value):
            # Send the request into the queue
            await queue_client.send_message(request.model_dump_json())
        else:
            worker = await Worker.create()
            await worker.process_request(request)

    except Exception as ex:
        raise HTTPException(500, ex)

    end_time = time.time()

    return f"Success : {end_time - start_time}"

if (not is_azure_environment()):
    # Run the app locally
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="debug", timeout_keep_alive=60)
    