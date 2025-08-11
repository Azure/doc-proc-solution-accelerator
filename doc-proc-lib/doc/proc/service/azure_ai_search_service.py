import logging
import os
from typing import List
import aiohttp

from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

from doc.proc.service.service_base import ServiceBase, ServiceExecutionError
from dependencies import get_config

logger = logging.getLogger("doc.proc.service.azure_ai_search_service") # need to specify the logger name as this module is loaded dynamically

config = get_config()
class AzureAISearchService(ServiceBase):
    """Azure AI Search service for managing AI search operations."""

    def __init__(self, name: str, type: str, settings:dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.account_name = settings.get('account_name')
        self.credential_type = settings.get('credential_type')
        self.credential_key = ''
        self.api_key = settings.get('api_key')
        self.api_version = settings.get('api_version')
        self.index_name = settings.get('index_name')

        if self.index_name.startswith('${') and self.index_name.endswith('}'):
            env_var_name = self.index_name[2:-1]
            self.index_name = config.get(env_var_name)
            if not self.index_name:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            raise ValueError("Settings key 'index_name' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")

        # Validate account name
        if not self.account_name:
            raise ValueError("Settings key 'account_name' is required")

        if self.account_name.startswith('${') and self.account_name.endswith('}'):
            env_var_name = self.account_name[2:-1]
            self.account_name = config.get(env_var_name)
            if not self.account_name:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            raise ValueError("Settings key 'account_name' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")

        self.endpoint = f"https://{self.account_name}.search.windows.net"

        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        if self.credential_type.startswith('${') and self.credential_type.endswith('}'):
            env_var_name = self.credential_type[2:-1]
            self.credential_type = config.get(env_var_name)
            if not self.credential_type:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            raise ValueError("Settings key 'credential_type' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")

        # Validate API key based on credential type
        if self.credential_type == 'azure_key_credential':
            self.api_key = settings.get('api_key')

            if not self.api_key:
                raise ValueError("Settings key 'api_key' is required for azure_key_credential")

            # Read the API key from environment variable
            if self.api_key.startswith('${') and self.api_key.endswith('}'):
                env_var_name = self.api_key[2:-1]
                self.api_key = config.get(env_var_name)
                if not self.api_key:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            else:
                raise ValueError("Settings key 'api_key' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")

        elif self.credential_type == 'default_azure_credential':
            self.api_key = ''
        
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}. Supported types are 'azure_key_credential' and 'default_azure_credential'.")

        # Validate api version
        if self.api_version not in ['2024-07-01', '2023-11-01', '2025-05-01-preview']:
            raise ValueError(f"Unsupported API version: {self.api_version}. Supported versions are '2024-07-01', '2023-11-01', and '2025-05-01-preview'.")

        # Validatre index name
        if self.index_name in ['', None]:
            raise ValueError("Settings key 'index_name' is required")

    
    async def get_auth_header_for_http_request(self):
        """Get the authentication header based on the credential type."""
        if self.credential_type == 'azure_key_credential':
            return {"api-key": self.api_key}
        elif self.credential_type == 'default_azure_credential':
            self._get_credentials()
            access_token = await self.aiocredential.get_token("https://search.azure.com/.default")
            return {"Authorization": f"Bearer {access_token.token}"}
        
        return {}


    async def test_connection(self) -> bool:
        """Test the connection to the Azure AI Search service."""
        try:
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.endpoint}/indexes('{self.index_name}')/search.stats?api-version={self.api_version}", 
                                       headers={"content-type": "application/json",
                                                **await self.get_auth_header_for_http_request()}) as resp:
                    status = resp.status
                    result = await resp.json()

            logger.debug(f"Connection test result: {result}")
            if status != 200:
                logger.error(f"Failed to connect to Azure AI Search Service. Status code: {status}, Response: {result}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to Azure AI Search Service: {str(e)}")
            raise ServiceExecutionError(f"Failed to connect to Azure AI Search Service: {str(e)}")

    async def write_documents(self, index_name: str, documents: List[dict]) -> dict:
        """Write documents to the specified Azure AI Search index."""
        if not documents:
            logger.warning("No documents to write to Azure AI Search index.")
            return {
                "status": "warning",
                "status_code": 400,
                "message": "No documents to write"
            }

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.endpoint}/indexes('{index_name}')/docs/search.index?api-version={self.api_version}"
                
                headers = {
                    "Content-Type": "application/json",
                    **await self.get_auth_header_for_http_request()
                }
                # Prepare the payload for indexing
                # Add the search action type
                for document in documents:
                    if not isinstance(document, dict):
                        logger.error(f"Invalid document format: {document}. Each document must be a dictionary.")
                        raise ValueError("Each document must be a dictionary.")

                    # Ensure each document has an 'id' field for indexing
                    if 'id' not in document:
                        logger.error(f"Document missing 'id' field: {document}")
                        raise ValueError("Each document must have an 'id' field.")

                    # Add the search action type
                    document['@search.action'] = 'mergeOrUpload'
                
                payload = {
                    "value": documents
                }

                async with session.post(url, json=payload, headers=headers) as resp:
                    status = resp.status
                    result = await resp.json()

                    if status != 200 and status != 201:
                        logger.error(f"Failed to write documents to Azure AI Search Index '{index_name}'. Status code: {status}, Response: {result}")
                        raise ServiceExecutionError(f"Failed to write documents to Azure AI Search Index '{index_name}'. Status code: {status}, Response: {result}")

            
            return result

        except Exception as e:
            logger.error(f"Error writing documents to Azure AI Search Index '{index_name}': {str(e)}")
            raise ServiceExecutionError(f"Error writing documents to Azure AI Search Index '{index_name}': {str(e)}")