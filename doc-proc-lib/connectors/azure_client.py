import logging

from azure.identity import ManagedIdentityCredential, AzureCliCredential, ChainedTokenCredential

class AzureClient():
    
    def _get_credential(self, credential):
        """
        Get the appropriate credential for authentication.
        
        :param credential: Credential for authentication (optional)
        :return: Credential object
        """
        if credential is None:
            try:
                credential = ChainedTokenCredential(
                    ManagedIdentityCredential(),
                    AzureCliCredential()
                )
                logging.debug("[blob] Initialized ChainedTokenCredential with ManagedIdentityCredential and AzureCliCredential.")
            except Exception as e:
                logging.error(f"[blob] Failed to initialize ChainedTokenCredential: {e}")
                raise
        else:
            logging.debug("[blob] Initialized BlobClient with provided credential.")
        return credential