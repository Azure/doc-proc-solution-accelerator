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

_settings = None  # Placeholder for app_settings import


async def check_cosmos_db_connectivity():
    """Check Cosmos DB connectivity before starting workers"""
    from azure.cosmos import exceptions
    from app.proxy.cosmos import CosmosDb
    
    logger = logging.getLogger("doc-proc-worker.run_worker")
    
    # Check if required settings are available
    if not _settings.COSMOS_DB_ENDPOINT:
        logger.fatal("❌ FATAL: COSMOS_DB_ENDPOINT is not configured")
        raise SystemExit("Cosmos DB endpoint is required but not configured. Please check your environment variables or Azure App Configuration.")
    
    if not _settings.COSMOS_DB_NAME:
        logger.fatal("❌ FATAL: COSMOS_DB_NAME is not configured") 
        raise SystemExit("Cosmos DB database name is required but not configured.")
    
    logger.info(f"🔍 Checking Cosmos DB connectivity...")
    logger.info(f"   - Endpoint: {_settings.COSMOS_DB_ENDPOINT}")
    logger.info(f"   - Database: {_settings.COSMOS_DB_NAME}")
    
    try:
        # Test basic connectivity
        cosmos_db = CosmosDb(endpoint=_settings.COSMOS_DB_ENDPOINT, database_name=_settings.COSMOS_DB_NAME)
        
        # Try to get database info - this will fail if we can't connect or authenticate
        database = cosmos_db.database
        database_properties = database.read()
        
        logger.info(f"✅ Successfully connected to Cosmos DB")
        logger.info(f"   - Database ID: {database_properties.get('id')}")
        
        # Test that we can access required containers
        required_containers = _settings.get_cosmos_db_containers()
        logger.info(f"🔍 Verifying access to {len(required_containers)} required containers...")
        
        for container_name in required_containers:
            try:
                container = database.get_container_client(container_name)
                # Try a simple query to test read access
                list(container.query_items("SELECT TOP 1 * FROM c", enable_cross_partition_query=True))
                logger.debug(f"   ✅ Container '{container_name}' is accessible")
            except exceptions.CosmosResourceNotFoundError:
                logger.warning(f"   ⚠️  Container '{container_name}' does not exist (will be created automatically)")
            except Exception as e:
                logger.error(f"   ❌ Failed to access container '{container_name}': {e}")
                raise
        
        logger.info("✅ Cosmos DB connectivity check passed")
        
    except exceptions.CosmosHttpResponseError as e:
        logger.fatal(f"❌ FATAL: Cosmos DB HTTP error (status {e.status_code}): {e.message}")
        if e.status_code == 401:
            raise SystemExit("Cosmos DB authentication failed. Please check your credentials and permissions.")
        elif e.status_code == 403:
            raise SystemExit("Cosmos DB access forbidden. Please check your account permissions.")
        elif e.status_code == 404:
            raise SystemExit(f"Cosmos DB database '{_settings.COSMOS_DB_NAME}' not found. Please verify the database exists.")
        else:
            raise SystemExit(f"Cosmos DB connection failed with status {e.status_code}: {e.message}")
    except Exception as e:
        logger.fatal(f"❌ FATAL: Unexpected error during Cosmos DB connectivity check: {e}")
        logger.fatal(f"Error type: {type(e).__name__}")
        raise SystemExit(f"Failed to connect to Cosmos DB: {e}")


async def run_single_worker():
    """Run a single queue worker (original behavior)"""
    from app.queue_worker import QueueWorker
    
    logger = logging.getLogger("doc-proc-worker.run_worker")

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
    from app.worker_pool import WorkerPoolManager
    
    logger = logging.getLogger("doc-proc-worker.run_worker")
    
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
    from app.log_setup import setup_logger
    
    global _settings
    _settings = app_settings 

    # Set up logging
    setup_logger()
    logger = logging.getLogger("doc-proc-worker.run_queue_worker")
    
    # Perform startup connectivity checks
    logger.info("🚀 Starting up worker process...")
    try:
        asyncio.run(check_cosmos_db_connectivity())
    except SystemExit:
        # Re-raise SystemExit to preserve the exit behavior
        raise
    except Exception as e:
        logger.fatal(f"❌ FATAL: Startup connectivity check failed: {e}")
        return 1
    
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
