#!/usr/bin/env python3
"""
Script to run the Azure Storage Queue worker.

This worker continuously polls an Azure Storage Queue for batch execution requests
and submits them to the Celery task queue for processing.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.queue_worker import QueueWorker
from app.logging import setup_logger


async def main():
    """Main entry point"""
    setup_logger()

    logger = logging.getLogger("doc-proc-worker.run_queue_worker")

    logger.info("Starting Azure Storage Queue Worker...")
    
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


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
