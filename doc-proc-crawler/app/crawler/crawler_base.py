from abc import abstractmethod
import os
import json
import traceback
import logging
import uuid

from typing import List, Literal, Optional
from pydantic import BaseModel
from datetime import datetime

from app.crawler.crawler_config import CrawlerConfig, SourceInstanceConfig

from doc.proc.models import content_identifier
from doc.proc.step.step_base import StepInputOutput
from doc.proc.source.source_base import SourceBase
from doc.proc.source.source_config import SourceConfig
from doc.proc.source.source_manager import get_source
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_processing_type import DocProcProcessingType
from doc.proc.models.docproc_pipeline_state import DocProcPipelineState
from doc.proc.models.docproc_state import DocProcState
from doc.proc.models.queue import QueueBatchExecutionRequest

from app.state.docproc_state_service import DocProcStateService
from app.state.blob_storage_state_service import BlobStorageDocProcStateService

from connectors import BlobQueueClient, CosmosDBClient, AzureBlobClient

logger = logging.getLogger(__name__)

class CrawlerExecutionResult(BaseModel):
    """Model for the output of a crawler execution."""
    crawler_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None  # Reason for failure or partial success, if applicable
    elapsed_time_secs: float
    summary_data: dict = {}  # Summary data for the crawler execution
    data: dict = {}  # Final data output from the crawler execution


class CrawlerExecutionError(Exception):
    """Custom exception for errors during crawler execution."""
    pass


class CrawlerConfigError(Exception):
    """Custom exception for errors in crawler configuration."""
    pass


class Crawler:
    """
        Base class for crawler execution, managing the configuration and steps.

        This class is responsible for loading the crawler configuration, initializing services,
        and executing the steps in the defined sequence.
        It provides methods to create a crawler instance from configuration and run the crawler with input data.

        !IMPORTANT!
        Do not instantiate this class directly; use the `create` method to ensure proper initialization and validation.

        Attributes:
            crawler_config (CrawlerConfig): Configuration for the crawler.
            sources_config (List[SourceConfig]): Configuration for sources used in the crawler.
    """
    docproc_state_service : DocProcStateService
    pipeline_name : str
    vault_id : str

    def __init__(self, crawler_config: CrawlerConfig, 
                 source_catalog_config: List[SourceConfig]=None,
                 **kwargs):
        """
        Initialize the Crawler instance with the provided configuration.
        !IMPORTANT!
        Do not instantiate this class directly; use the `create` method to ensure proper initialization and validation.
        """

        self.crawler_config = crawler_config
        self.source_catalog = source_catalog_config
        
        self.docproc_state_service = BlobStorageDocProcStateService(AzureBlobClient())

        if not self.crawler_config:
            raise CrawlerConfigError("Crawler configuration cannot be None")

        self.sources: List[SourceBase] = []

        self.queue_client = BlobQueueClient()    

    async def __load(self):
        """Load the crawler configuration and steps."""

        self.name = self.crawler_config.name
        self.description = self.crawler_config.description
        self.version = self.crawler_config.version
        self.execution_sequence = self.crawler_config.execution_sequence
        self.settings = self.crawler_config.settings

        if not self.name:
            raise CrawlerConfigError("Crawler name cannot be empty")

        if self.crawler_config.source_instances and self.source_catalog:
            await self.__load_sources()

    async def __load_sources(self):
        """Load sources based on the configuration."""

        logger.debug("Loading sources from configuration")

        if not self.source_catalog or not isinstance(self.source_catalog, list) or len(self.source_catalog) == 0:
            # do not raise an error if no sources are configured
            # this allows pipelines to run without sources if not needed
            return

        for source_instance_config in self.crawler_config.source_instances:

            if source_instance_config.enabled == False:
                logger.info(f"Source instance \"{source_instance_config.name}\" is disabled. Skipping loading.")
                continue

            logger.debug(f"Loading crawler source instance configuration: \"{source_instance_config.name}\" that references source catalog id \"{source_instance_config.source_catalog_id}\"")

            if not isinstance(source_instance_config, SourceInstanceConfig):
                raise TypeError(f"Source configuration must be an instance of SourceInstanceConfig, got \"{type(source_instance_config)}\"")

            source_config = next((s for s in self.source_catalog if s.id == source_instance_config.source_catalog_id), None)
            if not source_config:
                raise CrawlerConfigError(f"Source configuration for id \"{source_instance_config.source_catalog_id}\" not found in sources catalog.")

            source_instance = await get_source(
                source_config=source_config,
                instance_settings=source_instance_config.settings
            )

            if not source_instance:
                raise CrawlerConfigError(f"Source instance \"{source_config.name}\" could not be created from configuration in the catalog.")

            logger.info(f"Source instance \"{source_instance_config.name}\" loaded successfully.")

            if source_config.test_connection:
                logger.debug(f"Testing connection for source instance \"{source_instance_config.name}\"")
                if not await source_instance.test_connection():
                    raise CrawlerConfigError(f"Source instance \"{source_instance_config.name}\" failed to pass the connection test")

                logger.info(f"Source instance \"{source_instance_config.name}\" connection test passed successfully")

            self.sources.append({ "name": source_instance_config.name,
                                   "catalog_id": source_instance_config.source_catalog_id,
                                   "instance": source_instance
                                 })

    @staticmethod
    async def create(crawler_config: CrawlerConfig, 
                     source_catalog_config: List[SourceConfig] = None) -> "Crawler":
        """Factory method to create a Crawler instance from configuration."""

        logger.info("Creating crawler instance from configuration")

        if not crawler_config:
            raise CrawlerConfigError("Crawler configuration cannot be None")

        if not source_catalog_config or len(source_catalog_config) == 0:
            raise CrawlerConfigError("Source catalog cannot be None or empty")

        crawler_instance = Crawler(crawler_config=crawler_config, 
                                     source_catalog_config=source_catalog_config)

        # Load and validate the crawler configuration and steps.
        try:
            await crawler_instance.__load()
        except Exception as e:
            raise CrawlerConfigError(f"Error loading crawler from configuration: {str(e)}")

        logger.debug(f"Crawler instance '{crawler_instance.name}' created successfully.")
        return crawler_instance
    
    async def get_document(self, content_identifier : ContentIdentifier) -> dict:

        source = None

        for src in self.sources:
            if src['catalog_id'] == content_identifier.data_source_object_id:
                source = src
                break

        if (source):
            return await source['instance'].get_document(content_identifier)
        
        return None

    async def load_data(self) -> StepInputOutput:
        """Load data for the crawler."""
        logger.info(f"Loading data for crawler '{self.name}'")

        input_data = StepInputOutput(summary_data={}, data={})

        # Implement data loading logic here
        for source in self.sources:
            instance = source.get('instance')
            source_input_data = await instance.load_data()
            if not source_input_data:
                logger.warning(f"Source '{source.name}' returned no data.")
                continue
            
            # Merge or process input_data as needed
            input_data.data.update(source_input_data.data)
            logger.info(f"Loaded data from source '{instance.name}'")

        return input_data
    
    async def purge(self):
        logging.info("Starting purge job")

        for source in self.sources:
            try:
                logging.info(f"[{source}] Starting purge")
                source_instance : SourceBase = source['instance']
                
                items = self.docproc_state_service.get_source_items(source)

                step_list = [
                    {'id':'ai_search_purge_item',
                     'parameters' : {}
                    }
                ]

                for item in items:
                    try:
                        data = json.loads(item)
                        state = DocProcState(**data)
                        ci = state.content_identifier
                        ci.metadata = {}
                        document = await source_instance.get_content_metadata(ci.canonical_id)

                        if document == None:
                            request = DocProcRequest(content_identifier=ci, 
                                                        processing_type=DocProcProcessingType.asynchronous,
                                                        pipeline_object_id=self.name,
                                                        pipeline_name=self.name,
                                                        pipeline_execution_id=str(uuid.uuid4()),
                                                        steps = step_list
                                                        )
                            logging.info(f"[{source}] Sending content request - [{request.content_identifier.canonical_id}]")
                            await self.queue_client.send_message(request.model_dump_json())
                    except Exception as ex:
                        logging.error(ex)
            except Exception as ex:
                logging.error(ex)
    
    async def crawl(self):
        logging.info("Starting crawl job")
            
        for source in self.sources:
            logging.info(f"[{source}] Starting crawl")
            source_instance : SourceBase = source['instance']
            
            logging.info(f"[{source}] Getting item iterator")
            document_iterator = source_instance.get_items()

            document : ContentIdentifier
            for document in document_iterator:

                try:
                    document.data_source_object_id = source['catalog_id']
                    request = DocProcRequest(content_identifier=document, 
                                                processing_type=DocProcProcessingType.asynchronous,
                                                pipeline_object_id=self.name,
                                                pipeline_name=self.name,
                                                pipeline_execution_id=str(uuid.uuid4())
                                                )
                    
                    modified = True
                    deleted = False
                    
                    if (await self.docproc_state_service.has_state(request)):
                        state = await self.docproc_state_service.get_state(request)
                        modified, deleted = await source_instance.check_changes(request, state)

                    if (modified and not deleted) or source_instance.settings.get("reindex", False):
                        # Send the request into the queue
                        logging.info(f"[{source}] Sending content request - [{request.content_identifier.canonical_id}]")

                        request = QueueBatchExecutionRequest(
                            message_type="batch_execution_request",
                            pipeline_name=self.crawler_config.pipeline_name,
                            vault_id=self.crawler_config.vault_id,
                            documents = [document.model_dump()],
                            batch_id = str(uuid.uuid4()),
                            requested_by="crawler",
                        metadata={}
                        )
                        #await self.queue_client.send_message(request)
                        await self.queue_client.send_message(request.model_dump_json())
                except Exception as ex:
                    logging.error(ex)

    async def run(self) -> CrawlerExecutionResult:
        """Run the crawler with the given input data."""
        input_data = await self.load_data()

        logger.info(f"Starting crawler '{self.name}' execution with input data: {input_data.data}")

        context = CrawlerExecutionContext(crawler=self, sources=self.sources, start_time=datetime.now())

        output_data = input_data

        result_status = "NotStarted"

        if not isinstance(output_data, StepInputOutput):
            logger.error("Input data must be an instance of StepInputOutput")
            raise TypeError("Input data must be an instance of StepInputOutput")

        crawler_execution_result = CrawlerExecutionResult(crawler_name=self.name, result=result_status, elapsed_time_secs=0, data=output_data.data, summary_data=output_data.summary_data)

class CrawlerExecutionContext:
    """Context for pipeline execution, can be extended with more attributes as needed."""

    crawler : Crawler
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_source(self, source_name: str) -> Optional[SourceBase]:
        """Get a source by name from the execution context."""
        if not hasattr(self, 'sources') or not isinstance(self.sources, list):
            return None

        return next((source['instance'] for source in self.sources if source['name'] == source_name), None)
