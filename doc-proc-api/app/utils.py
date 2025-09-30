from functools import lru_cache
import logging

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("doc-proc-ui.app.utils")

@lru_cache(maxsize=1)
def get_azure_credential():
    """
    Get the appropriate credential for authentication.
        
    :return: Credential object
    """
    try:
        credential = DefaultAzureCredential(logging_enable=True)
        logger.debug(f"Initialized DefaultAzureCredential.")
        return credential
       
    except Exception as e:
        logger.error(f"Failed to initialize DefaultAzureCredential: {e}")
        raise
    
@lru_cache(maxsize=1)
def get_azure_credential_with_details():
    """
    Get the appropriate credential for authentication.
        
    :return: Credential object
    """
    try:
        credential = DefaultAzureCredential(logging_enable=True)
        logger.debug(f"Initialized DefaultAzureCredential.")
        
        token_details = _get_token_details(credential)
        if token_details:
            logger.debug(f"Token details: {token_details}")
        
        return credential, token_details
    except Exception as e:
        logger.error(f"Failed to initialize DefaultAzureCredential: {e}")
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