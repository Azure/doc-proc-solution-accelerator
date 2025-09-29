import logging
from functools import lru_cache

from azure.identity import ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential

logger = logging.getLogger("doc-proc-worker.app.utils")

@lru_cache(maxsize=1)
def get_azure_credential(credential=None):
    """
    Get the appropriate credential for authentication.
        
    :param credential: Credential for authentication (optional)
    :return: Credential object
    """
    from dependencies import get_config
    config = get_config()

    if credential is None:
        try:
            client_id = config.get('AZURE_CLIENT_ID', "")
            tenant_id = config.get('AZURE_TENANT_ID', "")

            credential = ChainedTokenCredential(
                ManagedIdentityCredential(client_id=client_id),
                AzureCliCredential(tenant_id=tenant_id)
            )
            logger.debug("Initialized Credential.")

        except Exception as e:
            logger.error(f"Failed to initialize Credential: {e}")
            raise
    else:
        logger.debug("Initialized with provided credential.")

    return credential

@lru_cache(maxsize=1)
def get_azure_credential_with_details():
    """
    Get the appropriate credential for authentication.
        
    :return: Credential object
    """
    try:
        credential = get_azure_credential()
        logger.debug(f"Initialized Credential.")
        
        token_details = _get_token_details(credential)
        if token_details:
            logger.debug(f"Token details: {token_details}")
        
        return credential, token_details
    except Exception as e:
        logger.error(f"Failed to initialize Credential: {e}")
        raise

@lru_cache(maxsize=1)
def _get_token_details(credential):
    if credential:
        try:
            token = credential.get_token("https://management.azure.com//.default")
            if token and token.token:
                import base64
                import json
                if "." in token.token:
                    base64_meta_data = token.token.split(".")[1]
                    padding_needed = -len(base64_meta_data) % 4
                    if padding_needed:
                        base64_meta_data += "=" * padding_needed
                    json_bytes = base64.urlsafe_b64decode(base64_meta_data)
                    json_string = json_bytes.decode("utf-8")
                    json_dict = json.loads(json_string)
                    upn = json_dict.get("upn", "unavailableUpn")
                    appid = json_dict.get("appid", "<unavailable>")
                    tid = json_dict.get("tid", "<unavailable>")
                    oid = json_dict.get("oid", "<unavailable>")
                    
                    return {
                        "client_id": appid,
                        "tenant_id": tid,
                        "upn": upn,
                        "object_id": oid
                    }
        except Exception as e:
            logger.error(f"Failed to decode token details: {e}")
    
    return None