"""
Multiprocessing worker pool manager for running multiple queue workers concurrently.

This module provides a WorkerPoolManager that spawns multiple worker processes,
each running an async queue worker. It handles graceful shutdown coordination
across all workers when termination signals are received.
"""

import asyncio
import logging
import multiprocessing as mp
import os
import signal
import sys
import time
from typing import Dict, List, Optional
from multiprocessing import Process, Queue
from multiprocessing.synchronize import Event as mp_Event
from dataclasses import dataclass
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.queue_worker import QueueWorker
from app.log_setup import setup_logger


@dataclass
class WorkerInfo:
    """Information about a worker process"""
    process: Process
    worker_id: str
    started_at: datetime
    pid: Optional[int] = None


class WorkerPoolManager:
    """
    Manages a pool of queue worker processes with graceful shutdown capabilities.
    
    Features:
    - Spawns multiple worker processes, each running an async queue worker
    - Handles SIGTERM and SIGINT for coordinated shutdown
    - Monitors worker health and restarts failed workers (optional)
    - Provides statistics and monitoring capabilities
    """
    
    def __init__(self, 
                 num_workers: int = None,
                 worker_restart: bool = True,
                 shutdown_timeout: int = 30,
                 health_check_interval: int = 10):
        """
        Initialize the worker pool manager.
        
        Args:
            num_workers: Number of worker processes to spawn (defaults to CPU count)
            worker_restart: Whether to restart failed workers automatically
            shutdown_timeout: Maximum time to wait for graceful shutdown (seconds)
            health_check_interval: Interval for checking worker health (seconds)
        """
        self.num_workers = num_workers or mp.cpu_count()
        self.worker_restart = worker_restart
        self.shutdown_timeout = shutdown_timeout
        self.health_check_interval = health_check_interval
        
        # Process management
        self.workers: Dict[str, WorkerInfo] = {}
        self.shutdown_event = mp.Event()
        self.manager_pid = os.getpid()
        
        # Statistics
        self.started_at = datetime.now(timezone.utc)
        self.shutdown_requested_at: Optional[datetime] = None
        
        # Logging
        self.logger = logging.getLogger("doc-proc-worker.pool_manager")
        
        # Signal handlers (only set in main process)
        if os.getpid() == self.manager_pid:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals"""
        signal_names = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}
        signal_name = signal_names.get(signum, str(signum))
        
        self.logger.info(f"Received {signal_name}, initiating graceful shutdown of worker pool...")
        self.shutdown_event.set()
        self.shutdown_requested_at = datetime.now(timezone.utc)
    
    def start(self):
        """
        Start the worker pool and monitor workers until shutdown.
        
        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        self.logger.info(f"Starting worker pool with {self.num_workers} workers")
        
        try:
            # Start all workers
            self._start_workers()
            
            # Monitor workers until shutdown
            self._monitor_workers()
            
            # Graceful shutdown
            self._shutdown_workers()
            
            self.logger.info("Worker pool shutdown completed successfully")
            return 0
            
        except KeyboardInterrupt:
            self.logger.info("Worker pool interrupted by user")
            self._shutdown_workers()
            return 0
        except Exception as e:
            self.logger.error(f"Fatal error in worker pool: {e}")
            self._emergency_shutdown()
            return 1
    
    def _start_workers(self):
        """Start all worker processes"""
        for i in range(self.num_workers):
            self._start_worker(i)
        
        self.logger.info(f"Started {len(self.workers)} worker processes")
    
    def _start_worker(self, worker_index: int) -> str:
        """
        Start a single worker process.
        
        Args:
            worker_index: Index of the worker (for naming)
            
        Returns:
            str: Worker ID of the started worker
        """
        worker_id = f"worker_{worker_index:02d}"
        
        # Create the worker process
        process = Process(
            target=_worker_process_main,
            args=(worker_id, self.shutdown_event),
            name=f"QueueWorker-{worker_id}"
        )
        
        # Start the process
        process.start()
        
        # Track the worker
        worker_info = WorkerInfo(
            process=process,
            worker_id=worker_id,
            started_at=datetime.now(timezone.utc),
            pid=process.pid
        )
        
        self.workers[worker_id] = worker_info
        
        self.logger.info(f"Started worker {worker_id} (PID: {process.pid})")
        return worker_id
    
    def _monitor_workers(self):
        """Monitor worker processes until shutdown is requested"""
        self.logger.info("Starting worker monitoring loop")
        
        while not self.shutdown_event.is_set():
            try:
                # Check worker health
                self._check_worker_health()
                
                # Sleep until next health check or shutdown
                for _ in range(self.health_check_interval):
                    if self.shutdown_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Error in worker monitoring: {e}")
                time.sleep(5)  # Brief pause before retrying
        
        self.logger.info("Worker monitoring stopped")
    
    def _check_worker_health(self):
        """Check health of all workers and restart failed ones if enabled"""
        failed_workers = []
        
        for worker_id, worker_info in self.workers.items():
            if not worker_info.process.is_alive():
                if worker_info.process.exitcode is not None:
                    self.logger.error(
                        f"Worker {worker_id} (PID: {worker_info.pid}) "
                        f"exited with code {worker_info.process.exitcode}"
                    )
                else:
                    self.logger.error(f"Worker {worker_id} (PID: {worker_info.pid}) is not alive")
                
                failed_workers.append(worker_id)
        
        # Restart failed workers if auto-restart is enabled
        if failed_workers and self.worker_restart and not self.shutdown_event.is_set():
            for worker_id in failed_workers:
                self.logger.info(f"Restarting failed worker {worker_id}")
                
                # Clean up the old worker
                old_worker = self.workers.pop(worker_id)
                old_worker.process.join(timeout=1)  # Brief wait for cleanup
                
                # Start a new worker with the same ID
                worker_index = int(worker_id.split('_')[1])
                self._start_worker(worker_index)
    
    def _shutdown_workers(self):
        """Gracefully shutdown all worker processes"""
        if not self.workers:
            return
        
        # Signal all workers to shut down
        self.shutdown_event.set()
        
        # Wait for workers to finish gracefully
        shutdown_start = time.time()
        still_running = list(self.workers.values())
        
        while still_running and (time.time() - shutdown_start) < self.shutdown_timeout:
            time.sleep(0.5)  # Check every 500ms
            
            # Update list of still running workers
            still_running = [
                worker for worker in still_running 
                if worker.process.is_alive()
            ]
        
        # Terminate any workers that didn't shut down gracefully
        for worker_info in still_running:
            self.logger.warning(
                f"Force terminating worker {worker_info.worker_id} "
                f"(PID: {worker_info.pid}) after {self.shutdown_timeout}s timeout"
            )
            worker_info.process.terminate()
        
        # Final join with brief timeout
        for worker_info in self.workers.values():
            worker_info.process.join(timeout=2)
        
        self.logger.info("All workers have been shut down")
    
    def _emergency_shutdown(self):
        """Emergency shutdown - terminate all workers immediately"""
        self.logger.error("Performing emergency shutdown of all workers")
        
        for worker_info in self.workers.values():
            if worker_info.process.is_alive():
                self.logger.error(f"Force killing worker {worker_info.worker_id}")
                worker_info.process.terminate()
        
        # Brief wait for termination
        time.sleep(1)
        
        # Kill any that are still alive
        for worker_info in self.workers.values():
            if worker_info.process.is_alive():
                worker_info.process.kill()
    
    def get_worker_stats(self) -> Dict[str, any]:
        """Get statistics about the worker pool"""
        alive_workers = sum(1 for w in self.workers.values() if w.process.is_alive())
        
        return {
            "manager_pid": self.manager_pid,
            "started_at": self.started_at.isoformat(),
            "num_workers_configured": self.num_workers,
            "num_workers_alive": alive_workers,
            "num_workers_total": len(self.workers),
            "shutdown_requested": self.shutdown_event.is_set(),
            "shutdown_requested_at": (
                self.shutdown_requested_at.isoformat() 
                if self.shutdown_requested_at else None
            ),
            "workers": {
                worker_id: {
                    "worker_id": info.worker_id,
                    "pid": info.pid,
                    "started_at": info.started_at.isoformat(),
                    "is_alive": info.process.is_alive(),
                    "exit_code": info.process.exitcode
                }
                for worker_id, info in self.workers.items()
            }
        }


def _worker_process_main(worker_id: str, shutdown_event: mp_Event):
    """
    Main entry point for worker processes.
    
    This function runs in each worker process and:
    1. Sets up logging
    2. Creates and starts a QueueWorker
    3. Monitors the shutdown event
    4. Handles graceful shutdown
    
    Args:
        worker_id: Unique identifier for this worker
        shutdown_event: Event to signal when shutdown is requested
    """
    # Set up logging for this worker process
    setup_logger()
    logger = logging.getLogger(f"doc-proc-worker.{worker_id}")
    
    logger.info(f"Starting worker process {worker_id} (PID: {os.getpid()})")
    
    try:
        # Create the queue worker
        worker = QueueWorker(worker_id=worker_id)
        
        # # Override the worker's signal handler to check our shutdown event
        # def shutdown_handler(signum, frame):
        #     logger.debug(f"Worker {worker_id} received signal {signum}")
        #     worker._shutdown_requested = True
        
        # signal.signal(signal.SIGINT, shutdown_handler)
        # signal.signal(signal.SIGTERM, shutdown_handler)
        
        # Run the worker in an async event loop with shutdown monitoring
        asyncio.run(_run_worker_with_shutdown_monitoring(worker, shutdown_event, logger))
        
        logger.info(f"Worker {worker_id} finished normally")
        
    except Exception as e:
        logger.error(f"Fatal error in worker {worker_id}: {e}")
        sys.exit(1)


async def _run_worker_with_shutdown_monitoring(
    worker: QueueWorker, 
    shutdown_event: mp_Event,
    logger: logging.Logger
):
    """
    Run the worker with shutdown event monitoring.
    
    This runs the worker's start() method while periodically checking
    if the shutdown event has been set.
    """
    # Create a task to monitor the shutdown event
    async def shutdown_monitor():
        while not shutdown_event.is_set():
            await asyncio.sleep(0.5)  # Check every 500ms
        
        logger.info(f"Shutdown event detected, requesting worker shutdown...")
        worker._shutdown_requested = True
    
    # Run both the worker and shutdown monitor concurrently
    monitor_task = asyncio.create_task(shutdown_monitor())
    worker_task = asyncio.create_task(worker.start())
    
    try:
        # Wait for either the worker to finish or shutdown to be requested
        done, pending = await asyncio.wait(
            [worker_task, monitor_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # If shutdown was requested, wait a bit for graceful worker shutdown
        if monitor_task in done:
            logger.info("Shutdown requested, waiting for worker to finish gracefully...")
            try:
                await asyncio.wait_for(worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Worker didn't shut down gracefully, cancelling...")
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    logger.debug("Worker task cancelled successfully")
        
    except asyncio.CancelledError:
        logger.debug("Worker monitoring cancelled")
        worker._shutdown_requested = True
        # Cancel both tasks
        monitor_task.cancel()
        worker_task.cancel()
        # Wait for cancellation to complete
        try:
            await asyncio.gather(monitor_task, worker_task, return_exceptions=True)
        except Exception:
            pass
    finally:
        # Clean up any remaining tasks
        for task in [monitor_task, worker_task]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass