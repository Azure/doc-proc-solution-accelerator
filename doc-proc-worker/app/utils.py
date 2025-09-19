import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any
import traceback

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("doc-proc-worker.app.utils")

def get_azure_credential(credential=None):
    """
    Get the appropriate credential for authentication.
        
    :param credential: Credential for authentication (optional)
    :return: Credential object
    """
    if credential is None:
        try:
            credential = DefaultAzureCredential()
            logger.debug("[blob] Initialized DefaultAzureCredential.")

        except Exception as e:
            logger.error(f"[blob] Failed to initialize DefaultAzureCredential: {e}")
            raise
    else:
        logger.debug("[blob] Initialized BlobClient with provided credential.")

    return credential

def run_in_event_loop(function, params) -> Any:
    """
    Celery task to execute a pipeline batch.
    
    Args:
        batch_execution_id: ID of the batch execution to process
    """
    try:
        # Run the async execution in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(function(**params))
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Failed to execute function: {str(e)}")
        logger.error(traceback.format_exc())
        raise
