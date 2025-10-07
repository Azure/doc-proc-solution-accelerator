#!/usr/bin/env python3
"""
Script to run Crawler worker(s) with distributed coordination.

This script runs a distributed crawler worker management system that:
1. Automatically discovers source instances from Cosmos DB
2. Uses lease-based coordination to prevent duplicate workers across machines
3. Dynamically starts/stops workers based on source instance changes
4. Provides configurable maximum worker limits per machine
5. Handles graceful shutdown and error recovery

The system eliminates the need for manual source instance ID specification
and provides intelligent load distribution across multiple machines.
"""

import asyncio
import argparse
import logging
import sys
import os
from typing import List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.settings import app_settings

from app.log_setup import setup_logger
setup_logger()
logger = logging.getLogger("doc-proc-crawler.run_crawler")


async def check_cosmos_db_connectivity():
    """Check Cosmos DB connectivity before starting workers"""
    from azure.cosmos import exceptions
    from app.proxy.cosmos import CosmosDb
        
    # Check if required settings are available
    if not app_settings.COSMOS_DB_ENDPOINT:
        logger.fatal("❌ FATAL: COSMOS_DB_ENDPOINT is not configured")
        raise SystemExit("Cosmos DB endpoint is required but not configured. Please check your environment variables or Azure App Configuration.")
    
    if not app_settings.COSMOS_DB_NAME:
        logger.fatal("❌ FATAL: COSMOS_DB_NAME is not configured") 
        raise SystemExit("Cosmos DB database name is required but not configured.")
    
    logger.info(f"🔍 Checking Cosmos DB connectivity...")
    logger.info(f"   - Endpoint: {app_settings.COSMOS_DB_ENDPOINT}")
    logger.info(f"   - Database: {app_settings.COSMOS_DB_NAME}")
    
    try:
        # Test basic connectivity
        cosmos_db = CosmosDb(endpoint=app_settings.COSMOS_DB_ENDPOINT, database_name=app_settings.COSMOS_DB_NAME)

        # Try to get database info - this will fail if we can't connect or authenticate
        database = cosmos_db.database
        database_properties = database.read()
        
        logger.info(f"✅ Successfully connected to Cosmos DB")
        logger.info(f"   - Database ID: {database_properties.get('id')}")
        
        # Test that we can access required containers
        required_containers = app_settings.get_cosmos_db_containers()
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
            raise SystemExit(f"Cosmos DB database '{app_settings.COSMOS_DB_NAME}' not found. Please verify the database exists.")
        else:
            raise SystemExit(f"Cosmos DB connection failed with status {e.status_code}: {e.message}")
    except Exception as e:
        logger.fatal(f"❌ FATAL: Unexpected error during Cosmos DB connectivity check: {e}")
        logger.fatal(f"Error type: {type(e).__name__}")
        raise SystemExit(f"Failed to connect to Cosmos DB: {e}")


async def run_distributed_crawler(max_workers: int = None):
    """Run distributed crawler with automatic source instance discovery and coordination"""
    from app.discovery.distributed_manager import DistributedWorkerManager
   
    logger.info("Starting distributed crawler worker management system...")
    
    # Create the distributed worker manager
    manager = DistributedWorkerManager(
        max_workers=max_workers or app_settings.CRAWLER_MAX_WORKERS,
        discovery_poll_interval=app_settings.CRAWLER_DISCOVERY_POLL_INTERVAL,
        lease_duration_minutes=app_settings.CRAWLER_LEASE_DURATION_MINUTES,
        lease_renewal_interval_minutes=app_settings.CRAWLER_LEASE_RENEWAL_INTERVAL_MINUTES
    )
    
    try:
        await manager.start()
        return 0
    except KeyboardInterrupt:
        logger.info("Distributed crawler manager interrupted by user")
        await manager.stop()
        return 0
    except Exception as e:
        logger.error(f"Distributed crawler manager failed: {e}")
        logger.exception(e)
        return 1
 

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Run Document Processor Crawler with distributed coordination",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                            # Run distributed crawler (recommended)
  %(prog)s --max-workers=3                            # Run distributed crawler with custom worker limit

  
The distributed mode automatically:
- Discovers source instances from Cosmos DB
- Coordinates with other machines using leases
- Scales workers up/down based on source instance changes
- Prevents duplicate processing across machines
        """
    )
    
    # Distributed mode arguments
    parser.add_argument(
        '--max-workers',
        type=int,
        default=None,
        help='Maximum number of workers for this machine (default: from config)'
    )
    
    args = parser.parse_args()
    
    # Perform startup connectivity checks
    logger.info("🚀 Starting up crawler process...")
    try:
        asyncio.run(check_cosmos_db_connectivity())
    except SystemExit:
        # Re-raise SystemExit to preserve the exit behavior
        raise
    except Exception as e:
        logger.fatal(f"❌ FATAL: Startup connectivity check failed: {e}")
        return 1

    # Default distributed mode
    logger.info("Running in distributed coordination mode")
    return asyncio.run(run_distributed_crawler(args.max_workers))


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
