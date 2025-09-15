import logging

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("doc-proc-ui.app.utils")

def get_azure_credential(credential=None):
    """
    Get the appropriate credential for authentication.
        
    :param credential: Credential for authentication (optional)
    :return: Credential object
    """
    if credential is None:
        try:
            credential = DefaultAzureCredential(logging_enable=True)
            logger.debug(f"Initialized DefaultAzureCredential.")

        except Exception as e:
            logger.error(f"Failed to initialize DefaultAzureCredential: {e}")
            raise
    else:
        logger.debug("Initialized BlobClient with provided credential.")

    return credential