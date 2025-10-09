import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.dependencies import get_cosmos_proxy, get_storage_queue_proxy
from app.proxy.cosmos import CosmosDb
from app.proxy.queue import StorageQueue
from app.sources.manager import SourceManager, SourceBase, SourceItemMetadata, SourceItem
from app.models.crawler import (
    SourceInstance, CrawlExecution, CrawlStatus, 
    CrawlerWorkerStats, CrawlResult, CrawlTriggerType
)
from doc.proc.models import ContentIdentifier
from app.settings import app_settings

class CrawlerWorker:
    """Async worker that processes a single source instance and crawls documents"""
    
    def __init__(self, source_instance_id: str, worker_id: Optional[str] = None):
        
        self.source_instance_id = source_instance_id
        self.worker_id = worker_id or f"crawler_{source_instance_id}_{uuid.uuid4().hex[:8]}"
        self.cosmos_proxy: Optional[CosmosDb] = None
        self.queue_proxy: Optional[StorageQueue] = None
        self.source_manager = SourceManager()
        self.source_instance: Optional[SourceInstance] = None
        self.source: Optional[SourceBase] = None
        self.vault: Optional[dict] = None
        
        self.stats = CrawlerWorkerStats(
            worker_id=self.worker_id,
            started_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        
        # Control flags
        self._shutdown_requested = False
        self._current_crawl_execution: Optional[CrawlExecution] = None
        
        # Logging configuration
        self.logger = logging.getLogger(f"doc-proc-crawler.app.{self.worker_id}")
    
    async def start(self):
        """Start the crawler worker for the specific source instance"""
        self.logger.info(f"Starting crawler worker: {self.worker_id} for source instance: {self.source_instance_id}")
        
        try:
            # Initialize services
            await self._initialize_services()
            
            if not self.cosmos_proxy:
                raise RuntimeError("Failed to initialize required services")
            
            # Load and initialize the source instance
            await self._load_source_instance()
            
            if not self.source_instance:
                raise RuntimeError(f"Source instance {self.source_instance_id} not found")
            
            # Main processing loop
            await self._run_processing_loop()
            
        except Exception as e:
            self.logger.error(f"Fatal error in crawler worker: {e}", exc_info=True, stack_info=True)
            raise
        finally:
            await self._cleanup()
    
    async def _initialize_services(self):
        """Initialize required services"""
        self.logger.info("Initializing services...")
        
        # Connect to Cosmos DB
        self.logger.debug("Setting up Cosmos DB Service...")
        self.cosmos_proxy = get_cosmos_proxy()
        
        self.logger.debug("Setting up Storage Queue Service...")
        self.queue_proxy = get_storage_queue_proxy()
        
        self.logger.info("Services initialized successfully")
    
    async def _load_source_instance(self):
        """Load the source instance configuration from Cosmos DB"""
        try:
            self.logger.info(f"Loading source instance: {self.source_instance_id}")
            
            container = self.cosmos_proxy.get_container(app_settings.COSMOS_DB_CONTAINER_SOURCE_INSTANCES)
            item = container.read_item(item=self.source_instance_id, partition_key=self.source_instance_id)
            
            # Convert to SourceInstance model
            self.source_instance = SourceInstance(**item)

            self.logger.debug(f"Source instance loaded: {self.source_instance.name}")

            # Get the vault that is associated with this source instance
            self.logger.debug("Retrieving associated vault for source instance...")
            vault = self._get_associated_vault()
            if not vault:
                raise RuntimeError(f"No Vault is associated with source instance {self.source_instance_id}. Cannot proceed with crawling.")
            self.vault = vault

            # Get catalog definition
            catalog_item = self.cosmos_proxy.get(
                id=self.source_instance.source_catalog_id,
                container=app_settings.COSMOS_DB_CONTAINER_SOURCE_CATALOG,
                partition_key=self.source_instance.source_catalog_id
            )
            if not catalog_item:
                raise RuntimeError(f"Source catalog {self.source_instance.source_catalog_id} not found for source instance {self.source_instance_id}")
            
            self.logger.debug(f"Catalog definition loaded: {catalog_item.get('name')}")
            
            # Create source using doc-proc-lib
            self.source = self.source_manager.create_source_from_instance(
                source_instance=item,
                catalog_definition=catalog_item
            )

            self.logger.info(f"Successfully loaded source instance and created source: {self.source.name}")

        except Exception as e:
            self.logger.error(f"Failed to load source instance {self.source_instance_id}: {e}")
            raise
    
    async def _run_processing_loop(self):
        """Main processing loop for continuous crawling of the source instance"""
        self.logger.info("Starting crawler processing loop for source instance...")

        if not self.source_instance or not self.source:
            raise RuntimeError("Source instance not loaded")

        crawl_interval_seconds = self._get_crawl_interval()
        while not self._shutdown_requested:
            try:
                # Check if source instance is enabled and ready for crawling
                if not self._should_crawl_now():
                    self.logger.info("Source instance interval for crawling not met, waiting...")

                    # Wait before next check
                    for _ in range(crawl_interval_seconds):
                        if self._shutdown_requested:
                            break
                        try:
                            await asyncio.sleep(1) # sleep for a second
                        except asyncio.CancelledError:
                            self.logger.debug("Sleep cancelled during shutdown")
                            self._shutdown_requested = True
                            break
                    continue

                # Perform crawl of this source instance
                await self._process_source_instance()

                # Wait before next crawl cycle
                crawl_interval = crawl_interval_seconds
                self.logger.info(f"Crawl completed. Waiting {crawl_interval} seconds before next crawl.")
                
                for _ in range(crawl_interval):
                    if self._shutdown_requested:
                        break
                    try:
                        await asyncio.sleep(1) # sleep for a second
                    except asyncio.CancelledError:
                        self.logger.debug("Sleep cancelled during shutdown")
                        self._shutdown_requested = True
                        break
                
            except asyncio.CancelledError:
                self.logger.debug("Processing loop cancelled during shutdown")
                self._shutdown_requested = True
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self.logger.exception(e)
                try:
                    # Continue after error - wait before retrying
                    await asyncio.sleep(crawl_interval_seconds)
                except asyncio.CancelledError:
                    self.logger.debug("Error recovery sleep cancelled during shutdown")
                    self._shutdown_requested = True
                    break
        
        self.logger.info("Processing loop shutdown complete")
    
    def _should_crawl_now(self) -> bool:
        """Check if the source instance should be crawled now"""
        if not self.source_instance.enabled:
            return False
        
        # Get the vault that is associated with this source instance
        self.logger.debug("Retrieving associated vault for source instance...")
        vault = self._get_associated_vault()
        if not vault:
            self.logger.error(f"No Vault is associated with source instance {self.source_instance_id}. Cannot proceed with crawling.")
            return False
        # set the vault
        self.vault = vault
        
        # Check crawler settings for interval
        crawl_interval_seconds = self._get_crawl_interval()
        
        # Check if the last crawl failed
        if self.source_instance.last_crawl_status == CrawlStatus.FAILED:
            return True
        
        # Check last crawl time
        if self.source_instance.last_crawl_at:
            try:
                last_crawl = datetime.fromisoformat(self.source_instance.last_crawl_at.replace('Z', '+00:00'))
                time_since_last = datetime.now(timezone.utc) - last_crawl
                if time_since_last.total_seconds() < crawl_interval_seconds:
                    return False
            except Exception as e:
                self.logger.warning(f"Error parsing last_crawl_at: {e}")
        
        return True
    
    def _get_crawl_interval(self) -> int:
        """Get the crawl interval in seconds"""
        crawler_settings = self.source_instance.crawler_settings or {}
        crawl_interval_minutes = crawler_settings.get('crawl_interval_minutes', 60) # Default to 60 minutes
        return crawl_interval_minutes * 60
    
    async def _process_source_instance(self):
        """Process the configured source instance"""
        crawl_execution = None
        start_time = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Processing source instance: {self.source_instance.id}")
                        
            # Create crawl execution record
            crawl_execution = CrawlExecution(
                id=str(uuid.uuid4()),
                source_instance_id=self.source_instance.id,
                vault_id=self.vault.get('id'),
                status=CrawlStatus.RUNNING,
                trigger_type=CrawlTriggerType.AUTO,
                worker_id=self.worker_id,
                started_at=start_time.isoformat()
            )
            
            # Save initial execution record
            await self._save_crawl_execution(crawl_execution)
            self._current_crawl_execution = crawl_execution
            
            # Update worker stats
            self.stats.current_source_instance_id = self.source_instance.id
            self.stats.current_crawl_execution_id = crawl_execution.id
            self.stats.processing_since = start_time
            self.stats.last_activity_at = start_time
            
            # Perform the actual crawling
            await self._crawl_source_instance(crawl_execution)
            
            # Mark execution as completed
            crawl_execution.status = CrawlStatus.COMPLETED
            crawl_execution.completed_at = datetime.now(timezone.utc).isoformat()
            crawl_execution.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Update source instance
            self.source_instance.last_crawl_at = crawl_execution.completed_at
            self.source_instance.last_crawl_status = CrawlStatus.COMPLETED
            self.source_instance.crawl_checkpoint = start_time.isoformat()
            self.source_instance.crawler_settings['checkpoint_time'] = self.source_instance.crawl_checkpoint
            await self._update_source_instance()
            
            # Update worker stats
            self.stats.total_crawls_processed += 1
            self.stats.total_documents_queued += crawl_execution.files_queued
            self.stats.total_files_processed += crawl_execution.files_processed
            
        except Exception as e:
            self.logger.error(f"Error processing source instance {self.source_instance.id}: {e}", exc_info=True)
            
            if crawl_execution:
                # Mark execution as failed
                crawl_execution.status = CrawlStatus.FAILED
                crawl_execution.error_message = str(e)
                crawl_execution.completed_at = datetime.now(timezone.utc).isoformat()
                crawl_execution.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                # Update source instance with error status
                self.source_instance.last_crawl_at = crawl_execution.completed_at
                self.source_instance.last_crawl_status = CrawlStatus.FAILED
                # Note: Don't set status to ERROR as it's handled in the API model differently
                await self._update_source_instance()
                
                self.stats.total_errors += 1
        
        finally:
            if crawl_execution:
                # Save final execution state
                await self._save_crawl_execution(crawl_execution)
            
            # Clear current processing state
            self._current_crawl_execution = None
            self.stats.current_source_instance_id = None
            self.stats.current_crawl_execution_id = None
            self.stats.processing_since = None
            self.stats.last_activity_at = datetime.now(timezone.utc)
    
    async def _crawl_source_instance(self, crawl_execution: CrawlExecution):
        """Perform the actual crawling of the source instance using doc-proc-lib"""
        try:
            if not self.source:
                raise ValueError("Source not initialized")
            
            # Test connection first
            if not await self.source_manager.test_source_connection(self.source):
                raise RuntimeError("Source connection test failed")
            
            # Get crawler settings
            crawler_settings = self.source_instance.crawler_settings or {}
            max_documents = crawler_settings.get('max_documents', 100) # Default to 100 documents
            file_filters = crawler_settings.get('file_filters', [])
            processing_batch_size = crawler_settings.get('processing_batch_size', 10) # Default batch size
            incremental = crawler_settings.get('incremental', True)
            checkpoint_time = crawler_settings.get('checkpoint_time', None)
            if checkpoint_time:
                try:
                    # Validate checkpoint time format
                    checkpoint_time = datetime.fromisoformat(checkpoint_time.replace('Z', '+00:00'))
                except Exception as e:
                    self.logger.warning(f"Invalid checkpoint_time format, ignoring: {checkpoint_time}")
                    checkpoint_time = None
            crawl_depth = crawler_settings.get('crawl_depth', 3)
            
            #TODO: implement checking for updates/deletions
            check_for_updates = crawler_settings.get('check_for_updates', False)
            
            self.logger.debug(f"Starting document discovery for source {self.source_instance.id}")
            discovered_items: List[SourceItemMetadata] = []
            
            # Discover documents using using source crawl method
            async for item_metadata in self.source.crawl(
                path=None,  # Start from root
                recursive=True,
                crawl_depth=crawl_depth,
                max_documents=max_documents,
                file_filters=file_filters,
                incremental=incremental,
                checkpoint_time=checkpoint_time
            ):
                discovered_items.append(item_metadata)
                
                # Apply limits if configured
                if len(discovered_items) >= max_documents:
                    self.logger.debug(f"Reached max documents limit: {max_documents}")
                    break
            
            crawl_execution.total_files_found = len(discovered_items)
            self.logger.debug(f"Discovered {len(discovered_items)} documents")
            
            # Process documents in batches
            batch_items = []
            for i, item_metadata in enumerate(discovered_items):
                try:
                    
                    # Add to batch
                    batch_items.append(item_metadata)

                    crawl_execution.files_processed += 1
                    
                    # Process batch when full or at end
                    if len(batch_items) >= processing_batch_size or i == len(discovered_items) - 1:
                        uploaded, queued = await self._upload_document_batch(batch_items)
                        
                        crawl_execution.files_queued += queued
                        crawl_execution.files_uploaded += uploaded
                        batch_items.clear()
                    
                    # Update progress periodically
                    if crawl_execution.files_processed % 10 == 0:
                        await self._save_crawl_execution(crawl_execution)
                
                except Exception as e:
                    self.logger.warning(f"Error processing batch: {e}")
                    crawl_execution.files_failed += len(batch_items)
                    continue
        
        except Exception as e:
            self.logger.error(f"Error during crawling: {e}")
            raise

    async def _upload_document_batch(self, batch_documents: List[SourceItemMetadata]) -> tuple[int,int]:
        """Upload a batch of documents to the vault"""
        # This would integrate with the vault/document storage system
        uploaded_docs = []
        queued_docs = []
        
        try:

            batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:6]}_{len(batch_documents)}_docs"
            self.logger.debug(f"Uploading batch {batch_id} with {len(batch_documents)} documents to vault '{self.vault.get('name')}'")
            
            uploaded_docs = await self._write_document_batch_to_vault(batch_id, batch_documents)
            
            queued_docs = await self._queue_documents_for_processing(batch_id, uploaded_docs)

        except Exception as e:
            self.logger.warning(f"Failed to upload batch: {e}")
            self.logger.exception(e)
            raise
            
        return (len(uploaded_docs), len(queued_docs))

    async def _write_document_batch_to_vault(self, batch_id: str, batch_documents: List[SourceItemMetadata]) -> int:
        """Write a batch of documents to the vault"""
      
        docs_written = []
        
        for doc_data in batch_documents:
            try:
                content_identifier: ContentIdentifier = doc_data.content_identifier
                if not content_identifier:
                    raise ValueError("Document Item Metadata missing content identifier")

                document = {
                    "id": content_identifier.unique_id,
                    "vault_id": self.vault.get('id'),
                    "name": content_identifier.path,
                    "content_id": {
                        **content_identifier.model_dump()
                    },
                    "submit_date": datetime.now(timezone.utc).isoformat(),
                    "source" : "crawler",
                    "status": "queued",
                    "metadata": {
                        "name": doc_data.name,
                        "size": doc_data.size,
                        "modified_date": doc_data.modified_date.isoformat() if doc_data.modified_date else None,
                        "created_date": doc_data.created_date.isoformat() if doc_data.created_date else None,
                        "content_type": doc_data.content_type,
                        "etag": doc_data.etag,
                        "source_instance_id": self.source_instance.id,
                        "source_instance_name": self.source_instance.name,
                        "correlation_id": str(uuid.uuid4()),
                        "batch_id": batch_id,
                        "processing_attempts": 1,
                        "last_processing_attempt_at": datetime.now(timezone.utc).isoformat()
                    }
                }

                self.cosmos_proxy.upsert(container=app_settings.COSMOS_DB_CONTAINER_VAULT_DOCUMENTS, item=document)
                
                docs_written.append(document)

            except Exception as e:
                self.logger.warning(f"Failed to upload document {doc_data.content_identifier}: {e}")
                continue

        return docs_written

    async def _queue_documents_for_processing(self, batch_id: str, batch_documents: List[Dict]) -> List[Dict]:
        """Queue documents for further processing"""
        # This would integrate with the document processing queue system
        queued_docs = []
        
        try:
            if not self.queue_proxy:
                raise ValueError("Queue proxy not initialized")
            
            if not self.vault:
                raise ValueError("Vault information not available for queuing documents")

            if not batch_documents and len(batch_documents) == 0:
                raise ValueError("Documents list cannot be empty")
                
            # Create documents info list
            _documents = [{"id": doc.get('content_id')} for doc in batch_documents if doc.get('content_id')]

            self.logger.debug(f"Queueing {len(_documents)} documents in vault '{self.vault.get('name')}' for processing in pipeline '{self.vault.get('pipeline_name')}'")

            # create message content
            message = {
                "message_type": "batch_execution_request",
                "pipeline_name": self.vault.get('pipeline_name'),
                "vault_id": self.vault.get('id'),
                "documents": _documents,
                "batch_id": batch_id,
                "priority": 0,
                "metadata": {
                    "document_count": len(_documents),
                    "vault_name": self.vault.get('name'),
                },
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "requested_by": "system",
                "correlation_id": str(uuid.uuid4())
            }

            async with self.queue_proxy as queue:
                await queue.send_message(message)

            queued_docs.extend(_documents)

        except Exception as e:
            self.logger.error(f"Error queuing documents for processing: {e}")
            raise
        
        return queued_docs
    
    async def _update_source_instance(self):
        """Update source instance in Cosmos DB"""
        try:
            instance_dict = self.source_instance.model_dump()
            self.cosmos_proxy.upsert(container=app_settings.COSMOS_DB_CONTAINER_SOURCE_INSTANCES, item=instance_dict)
        except Exception as e:
            self.logger.error(f"Error updating source instance {self.source_instance.id}: {e}")
    
    async def _save_crawl_execution(self, crawl_execution: CrawlExecution):
        """Save crawl execution to Cosmos DB"""
        try:
            execution_dict = crawl_execution.model_dump()
            execution_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
            self.cosmos_proxy.upsert(container=app_settings.COSMOS_DB_CONTAINER_CRAWL_EXECUTIONS, item=execution_dict)
        except Exception as e:
            self.logger.error(f"Error saving crawl execution {crawl_execution.id}: {e}")

    def _get_associated_vault(self) -> dict:
        """Get the vault associated with this source instance"""
        try:
            query = "SELECT * FROM c WHERE c.source_instance_name = @source_instance_name"
            parameters = [
                {"name": "@source_instance_name", "value": self.source_instance.name}
            ]
            vaults = self.cosmos_proxy.list(app_settings.COSMOS_DB_CONTAINER_VAULTS, query=query, parameters=parameters)
            if vaults and len(vaults) > 0:
                    return vaults[0]
                    
        except Exception as e:
            self.logger.error(f"Error retrieving associated vault: {e}")
    
    async def _cleanup(self):
        """Clean up worker resources"""
        self.logger.info(f"Cleaning up crawler worker: {self.worker_id}")
        
        # Cancel current crawl if active
        if self._current_crawl_execution:
            self.logger.info("Cancelling active crawl")
            self._current_crawl_execution.status = CrawlStatus.CANCELLED
            self._current_crawl_execution.completed_at = datetime.now(timezone.utc).isoformat()
            self._current_crawl_execution.duration_seconds = (datetime.now(timezone.utc) - datetime.fromisoformat(self._current_crawl_execution.started_at.replace('Z', '+00:00'))).total_seconds()
            await self._save_crawl_execution(self._current_crawl_execution)
        
        # Clean up source connection
        if self.source:
            try:
                if hasattr(self.source, 'close'):
                    await self.source.close()
            except Exception as e:
                self.logger.warning(f"Error closing source connection: {e}")
        
        self.logger.info("Crawler worker cleanup completed")
    
    def request_shutdown(self):
        """Request graceful shutdown of the worker"""
        self.logger.info(f"Shutdown requested for crawler worker: {self.worker_id}")
        self._shutdown_requested = True