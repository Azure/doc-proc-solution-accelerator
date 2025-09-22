#!/usr/bin/env python3
"""
Script to run Azure Storage Queue worker(s).

This script can run either:
1. A single queue worker (default behavior, backward compatible)
2. A multiprocessing pool of workers (when --pool flag is used)

The multiprocessing pool provides better performance for high-throughput scenarios
and includes graceful shutdown handling across multiple worker processes.
"""

import asyncio
import argparse
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.queue_worker import QueueWorker
from app.worker_pool import WorkerPoolManager
from app.log_setup import setup_logger

_settings = None  # Placeholder for app_settings import

async def run_single_worker():
    """Run a single queue worker (original behavior)"""
    logger = logging.getLogger("doc-proc-worker.run_queue_worker")

    logger.info("Starting single Azure Storage Queue Worker...")
    
    # Create and start the worker
    worker = QueueWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Queue worker interrupted by user")
    except Exception as e:
        logger.error(f"Queue worker failed: {e}")
        return 1
    
    return 0


def run_worker_pool():
    """Run a multiprocessing pool of workers"""
    logger = logging.getLogger("doc-proc-worker.run_queue_worker")
    
    # Determine number of workers
    num_workers = _settings.WORKER_POOL_SIZE
    if num_workers <= 0:
        import multiprocessing as mp
        num_workers = mp.cpu_count()
    
    logger.info(f"Starting multiprocessing queue worker pool...")
    logger.info(f"Configuration:")
    logger.info(f"  - Workers: {num_workers}")
    logger.info(f"  - Auto-restart: {_settings.WORKER_AUTO_RESTART}")
    logger.info(f"  - Shutdown timeout: {_settings.WORKER_SHUTDOWN_TIMEOUT}s")
    logger.info(f"  - Health check interval: {_settings.WORKER_HEALTH_CHECK_INTERVAL}s")
    
    # Create and start the worker pool manager
    pool_manager = WorkerPoolManager(
        num_workers=num_workers,
        worker_restart=_settings.WORKER_AUTO_RESTART,
        shutdown_timeout=_settings.WORKER_SHUTDOWN_TIMEOUT,
        health_check_interval=_settings.WORKER_HEALTH_CHECK_INTERVAL
    )
    
    try:
        return pool_manager.start()
    except Exception as e:
        logger.error(f"Worker pool failed with error: {e}")
        return 1


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Run Azure Storage Queue worker(s)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run single worker (default)
  %(prog)s --pool             # Run multiprocessing pool
  %(prog)s --pool --workers 4 # Run pool with 4 workers
        """
    )
    
    parser.add_argument(
        '--pool', 
        action='store_true',
        help='Run multiprocessing pool of workers instead of single worker'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        help='Number of workers in pool (defaults to CPU count, only used with --pool)'
    )
    
    parser.add_argument(
        '--no-restart',
        action='store_true',
        help='Disable automatic restart of failed workers (only used with --pool)'
    )
    
    args = parser.parse_args()
    
    # get app_settings to ensure config is loaded
    from app.settings import app_settings
    _settings = app_settings 

    # Set up logging
    setup_logger()
    logger = logging.getLogger("doc-proc-worker.run_queue_worker")
    
    # Override settings from command line arguments
    if args.workers:
        _settings.WORKER_POOL_SIZE = args.workers
    if args.no_restart:
        _settings.WORKER_AUTO_RESTART = False

    if args.pool:
        # Run multiprocessing pool
        return run_worker_pool()
    else:
        # Run single worker (default, backward compatible)
        return asyncio.run(run_single_worker())


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
