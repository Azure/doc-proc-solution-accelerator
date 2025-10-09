"""
Distributed Worker Manager

This module implements the main worker management system that coordinates
source instance discovery, lease acquisition, and source worker lifecycle management
across multiple machines.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

# Import from crawler models (which imports from doc-proc-api)
from app.models.crawler import SourceInstance

from app.discovery.source_discovery import SourceInstanceDiscovery
from app.discovery.source_monitor import SourceInstanceMonitor
from app.discovery.lease_manager import LeaseManager, WorkerLease
from app.crawler_worker import CrawlerWorker
from app.settings import app_settings

logger = logging.getLogger(f"doc-proc-crawler.distributed_worker_manager")

@dataclass
class ManagedWorker:
    """Information about a managed worker process"""
    source_instance_id: str
    source_instance: SourceInstance
    worker: CrawlerWorker
    lease: WorkerLease
    task: asyncio.Task
    started_at: datetime
    status: str  # 'starting', 'running', 'stopping', 'stopped', 'failed'


class DistributedWorkerManager:
    """
    Manages crawler workers across distributed machines with lease-based coordination.
    
    Features:
    - Automatic source instance discovery from Cosmos DB
    - Lease-based coordination to prevent duplicate workers
    - Dynamic worker scaling based on source instance changes
    - Configurable maximum workers per machine
    - Graceful shutdown and error handling
    """
    
    def __init__(self, max_workers: int, 
                 discovery_poll_interval: int,
                 lease_duration_minutes: int,
                 lease_renewal_interval_minutes: int):
        
        self.max_workers = max_workers
        self.discovery_poll_interval = discovery_poll_interval
               
        # Core components
        self.source_discovery = SourceInstanceDiscovery(
            cosmos_endpoint=app_settings.COSMOS_DB_ENDPOINT,
            database_name=app_settings.COSMOS_DB_NAME,
            container_name=app_settings.COSMOS_DB_CONTAINER_SOURCE_INSTANCES
        )
        
        self.source_monitor = SourceInstanceMonitor(
            discovery=self.source_discovery,
            poll_interval=discovery_poll_interval
        )
        
        self.lease_manager = LeaseManager(
            cosmos_endpoint=app_settings.COSMOS_DB_ENDPOINT,
            database_name=app_settings.COSMOS_DB_NAME,
            container_name=app_settings.COSMOS_DB_CONTAINER_WORKER_LEASES,
            lease_duration_minutes=lease_duration_minutes,
            renewal_interval_minutes=lease_renewal_interval_minutes
        )
        
        # Worker management
        self._managed_workers: Dict[str, ManagedWorker] = {}
        self._running = False
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lease_retry_task: Optional[asyncio.Task] = None
        
        # Register callbacks
        self.source_monitor.on_instance_added(self._handle_source_added)
        self.source_monitor.on_instance_removed(self._handle_source_removed)
        self.source_monitor.on_instance_updated(self._handle_source_updated)
        
    async def start(self):
        """Start the distributed worker manager"""
        if self._running:
            logger.warning("Worker manager is already running")
            return
            
        logger.info("Starting distributed worker manager...")
        logger.info(f"Configuration:")
        logger.info(f"  - Max workers: {self.max_workers}")
        logger.info(f"  - Discovery interval: {self.discovery_poll_interval}s")
        logger.info(f"  - Machine ID: {self.lease_manager.machine_id}")
        
        self._running = True
        
        try:
            # Initialize components
            async with self.lease_manager:
                async with self.source_discovery:
                    
                    # Start monitoring source instances
                    await self.source_monitor.start()
                    
                    # Start background cleanup task
                    self._cleanup_task = asyncio.create_task(self._cleanup_loop())
                    
                    # Start background lease retry task (more frequent than cleanup)
                    self._lease_retry_task = asyncio.create_task(self._lease_retry_loop())
                    
                    logger.info("Distributed worker manager started successfully")
                    
                    # Process initial source instances
                    await self._process_initial_source_instances()
                    
                    # Keep running until stopped
                    while self._running:
                        await asyncio.sleep(1)
                        
        except Exception as e:
            logger.error(f"Error in worker manager: {e}")
            raise
        finally:
            await self._shutdown()
            
    async def stop(self):
        """Stop the worker manager gracefully"""
        if not self._running:
            return
            
        logger.info("Stopping distributed worker manager...")
        self._running = False
        
    async def _shutdown(self):
        """Internal shutdown logic"""
        try:
            # Stop source monitor
            await self.source_monitor.stop()
            
            # Stop all workers
            await self._stop_all_workers()
            
            # Stop background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                    
            if self._lease_retry_task:
                self._lease_retry_task.cancel()
                try:
                    await self._lease_retry_task
                except asyncio.CancelledError:
                    pass
                    
            logger.info("Distributed worker manager stopped")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    async def _process_initial_source_instances(self):
        """Process source instances discovered during startup"""
        try:
            current_instances = self.source_discovery.get_current_instances()
            logger.info(f"Processing {len(current_instances)} initial source instances")
            
            for source_instance in current_instances.values():
                await self._handle_source_added(source_instance)
                
        except Exception as e:
            logger.error(f"Error processing initial source instances: {e}")
            
    async def _handle_source_added(self, source_instance: SourceInstance):
        """Handle when a new source instance is discovered"""
        source_id = source_instance.id

        logger.info(f"New source instance detected: {source_id}")

        # Check if source instance is disabled
        if not source_instance.enabled:
            logger.info(f"Source instance {source_id} is disabled, skipping worker creation")
            return

        # Check if source instance is a system instance
        if source_instance.is_system:
            logger.info(f"Source instance {source_id} is a system instance, skipping worker creation")
            return

        # Check if we're already managing this source
        if source_id in self._managed_workers:
            logger.debug(f"Already managing worker for source: {source_id}")
            return
            
        # Check if we've reached max workers
        if len(self._managed_workers) >= self.max_workers:
            logger.warning(f"Max workers ({self.max_workers}) reached, cannot start worker for {source_id}")
            return
            
        # Try to acquire lease for this source instance
        try:
            lease = await self.lease_manager.try_acquire_lease(source_id)
            
            if lease:
                await self._start_worker(source_instance, lease)
            else:
                logger.debug(f"Could not acquire lease for source instance: {source_id}")
                
        except Exception as e:
            logger.error(f"Error handling new source instance {source_id}: {e}")
            
    async def _handle_source_removed(self, source_instance_id: str):
        """Handle when a source instance is removed"""
        logger.info(f"Source instance removed: {source_instance_id}")

        if source_instance_id in self._managed_workers:
            await self._stop_worker(source_instance_id)
            
    def _has_significant_changes(self, old_instance: SourceInstance, new_instance: SourceInstance) -> bool:
        """
        Check if the source instance has significant changes that require worker restart.
        
        Significant changes include:
        - Connection settings changes
        - Crawler configuration changes  
        - Source catalog changes
        - Enabled/disabled status changes
        - Test connection behavior changes
        """
            
        # Check if enabled status changed
        if old_instance.enabled != new_instance.enabled:
            logger.info(f"Enabled status changed: {old_instance.enabled} -> {new_instance.enabled}")
            return True
            
        # Check if connection settings changed
        if old_instance.settings != new_instance.settings:
            logger.info(f"Instance settings changed for source: {new_instance.id}")
            return True
            
        # Check if crawler settings changed
        if old_instance.crawler_settings != new_instance.crawler_settings:
            logger.info(f"Crawler settings changed for source: {new_instance.id}")
            return True
            
        # No significant changes detected
        return False

    async def _handle_source_updated(self, source_instance: SourceInstance):
        """Handle when a source instance is updated"""
        source_id = source_instance.id
        logger.debug(f"Source instance updated: {source_id}")
        
        if source_id in self._managed_workers:
            managed_worker = self._managed_workers[source_id]
            old_instance = managed_worker.source_instance
            
            # Special case: if source becomes disabled, stop the worker
            if not source_instance.enabled:
                logger.info(f"Source instance {source_id} has been disabled, stopping worker...")
                await self._stop_worker(source_id)
                return
            
            # Check for significant changes that require worker restart
            if self._has_significant_changes(old_instance, source_instance):
                logger.info(f"Significant changes detected for source {source_id}, restarting worker...")
                
                # Stop the current worker
                await self._stop_worker(source_id)
                
                # Start a new worker with updated configuration
                # Try to acquire lease again (should succeed since we just released it)
                try:
                    lease = await self.lease_manager.try_acquire_lease(source_id)
                    if lease:
                        await self._start_worker(source_instance, lease)
                    else:
                        logger.warning(f"Could not reacquire lease for source {source_id} after restart")
                except Exception as e:
                    logger.error(f"Error restarting worker for source {source_id}: {e}")
            else:
                # No significant changes, just update the source instance data
                managed_worker.source_instance = source_instance
                logger.debug(f"Updated source instance data for worker: {source_id}")
        else:
            # Source instance was updated but we're not managing a worker for it
            # This could happen if the source was previously disabled and is now enabled
            if source_instance.enabled:
                logger.info(f"Previously unmanaged source {source_id} is now enabled, attempting to start worker...")
                await self._handle_source_added(source_instance)

    async def _start_worker(self, source_instance: SourceInstance, lease: WorkerLease):
        """Start a crawler worker for a source instance"""
        source_id = source_instance.id
        
        try:
            logger.info(f"Starting worker for source instance: {source_id}")
            
            # Create worker
            worker = CrawlerWorker(source_instance_id=source_id)
            
            # Create managed worker record
            managed_worker = ManagedWorker(
                source_instance_id=source_id,
                source_instance=source_instance,
                worker=worker,
                lease=lease,
                task=None,  # Will be set below
                started_at=datetime.now(timezone.utc),
                status='starting'
            )
            
            # Start worker task
            task = asyncio.create_task(self._run_worker(managed_worker))
            managed_worker.task = task
            
            # Track the worker
            self._managed_workers[source_id] = managed_worker
            managed_worker.status = 'running'

            logger.info(f"Worker started for source instance: {source_id}")

        except Exception as e:
            logger.error(f"Failed to start worker for {source_id}: {e}")

            # Release the lease if worker failed to start
            try:
                await self.lease_manager.release_lease(source_id)
            except Exception as lease_error:
                logger.error(f"Failed to release lease after worker start failure: {lease_error}")
                
    async def _run_worker(self, managed_worker: ManagedWorker):
        """Run a worker with monitoring and error handling"""
        source_id = managed_worker.source_instance_id
        
        try:
            logger.debug(f"Running worker for source instance: {source_id}")
            await managed_worker.worker.start()
            
        except asyncio.CancelledError:
            logger.info(f"Worker cancelled for source instance: {source_id}")
            managed_worker.status = 'stopped'
            
        except Exception as e:
            logger.error(f"Worker failed for source instance {source_id}: {e}")
            managed_worker.status = 'failed'
            
            # Release the lease so another worker can take over
            try:
                await self.lease_manager.release_lease(source_id)
            except Exception as lease_error:
                logger.error(f"Failed to release lease after worker failure: {lease_error}")
                
        finally:
            # Clean up the managed worker
            if source_id in self._managed_workers:
                del self._managed_workers[source_id]
                
    async def _stop_worker(self, source_instance_id: str):
        """Stop a worker gracefully"""
        if source_instance_id not in self._managed_workers:
            return
            
        managed_worker = self._managed_workers[source_instance_id]
        
        try:
            logger.info(f"Stopping worker for source instance: {source_instance_id}")
            managed_worker.status = 'stopping'
            
            # Request worker shutdown
            managed_worker.worker.request_shutdown()
            
            # Cancel the task
            if managed_worker.task and not managed_worker.task.done():
                managed_worker.task.cancel()
                
                try:
                    await asyncio.wait_for(managed_worker.task, timeout=30)
                except asyncio.TimeoutError:
                    logger.warning(f"Worker for {source_instance_id} did not stop gracefully within timeout")
                except asyncio.CancelledError:
                    pass
                    
            # Release the lease
            await self.lease_manager.release_lease(source_instance_id)
            
            # Remove from managed workers
            if source_instance_id in self._managed_workers:
                del self._managed_workers[source_instance_id]

            logger.info(f"Worker stopped for source instance: {source_instance_id}")

        except Exception as e:
            logger.error(f"Error stopping worker for {source_instance_id}: {e}")

    async def _stop_all_workers(self):
        """Stop all managed workers"""
        worker_ids = list(self._managed_workers.keys())
        
        if worker_ids:
            logger.info(f"Stopping {len(worker_ids)} workers...")
            
            # Stop all workers concurrently
            stop_tasks = [self._stop_worker(worker_id) for worker_id in worker_ids]
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run cleanup every 5 minutes
                
                if not self._running:
                    break
                    
                # Cleanup expired leases
                await self.lease_manager.cleanup_expired_leases()
                
                # Monitor worker health and restart failed workers
                await self._monitor_worker_health()
                
                # Attempt to acquire leases for source instances without workers
                await self._retry_lease_acquisition()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                
    async def _monitor_worker_health(self):
        """Monitor worker health and restart failed workers if needed"""
        failed_workers = []
        
        for source_id, managed_worker in self._managed_workers.items():
            if managed_worker.task.done():
                try:
                    # Check if task completed with an exception
                    await managed_worker.task
                except Exception as e:
                    logger.error(f"Worker {source_id} failed: {e}")
                    failed_workers.append(source_id)
                    
        # Handle failed workers
        for source_id in failed_workers:
            logger.info(f"Restarting failed worker for source: {source_id}")
            await self._stop_worker(source_id)  # Clean up
            
            # Try to restart if we still have the source instance
            current_instances = self.source_discovery.get_current_instances()
            if source_id in current_instances:
                await self._handle_source_added(current_instances[source_id])
                
    async def _retry_lease_acquisition(self):
        """Attempt to acquire leases for source instances without active workers"""
        if len(self._managed_workers) >= self.max_workers:
            return  # Already at capacity
            
        try:
            current_instances = self.source_discovery.get_current_instances()
            
            # Find source instances that don't have active workers
            unmanaged_instances = []
            for source_id, source_instance in current_instances.items():
                if (source_id not in self._managed_workers and 
                    source_instance.enabled and 
                    not source_instance.is_system):
                    unmanaged_instances.append(source_instance)
            
            if not unmanaged_instances:
                return
                
            logger.debug(f"Attempting to acquire leases for {len(unmanaged_instances)} unmanaged source instances")
            
            # Try to acquire leases for unmanaged instances
            for source_instance in unmanaged_instances:
                if len(self._managed_workers) >= self.max_workers:
                    break  # Reached capacity
                    
                try:
                    lease = await self.lease_manager.try_acquire_lease(source_instance.id)
                    
                    if lease:
                        logger.info(f"Successfully acquired lease for previously unmanaged source: {source_instance.id}")
                        await self._start_worker(source_instance, lease)
                        
                except Exception as e:
                    logger.debug(f"Failed to acquire lease for {source_instance.id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in retry lease acquisition: {e}")
            
    async def _lease_retry_loop(self):
        """More frequent lease retry loop (runs every 60 seconds)"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute for lease opportunities
                
                if not self._running:
                    break
                    
                # Only retry if we have capacity for more workers
                if len(self._managed_workers) < self.max_workers:
                    await self._retry_lease_acquisition()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lease retry loop: {e}")
                
    def get_worker_status(self) -> Dict[str, dict]:
        """Get status of all managed workers"""
        status = {}
        
        for source_id, managed_worker in self._managed_workers.items():
            status[source_id] = {
                'source_name': managed_worker.source_instance.name,
                'status': managed_worker.status,
                'started_at': managed_worker.started_at.isoformat(),
                'machine_id': managed_worker.lease.machine_id,
                'worker_id': managed_worker.lease.worker_id
            }
            
        return status
        
    def get_manager_stats(self) -> dict:
        """Get manager statistics"""
        return {
            'max_workers': self.max_workers,
            'active_workers': len(self._managed_workers),
            'machine_id': self.lease_manager.machine_id,
            'process_id': self.lease_manager.process_id,
            'running': self._running,
            'discovery_poll_interval': self.discovery_poll_interval
        }