import logging

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("doc-proc-worker.app.azure_resource")

# TODO: make instead part of utils
class AzureResource():
    
    def _get_credential(self, credential=None):
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