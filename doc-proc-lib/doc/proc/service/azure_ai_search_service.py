import logging
import os
import json
import aiohttp
import requests
import pandas as pd

from azure.core.exceptions import AzureError
from datetime import datetime as Timestamp
from typing import Dict, Optional, Any, List
from configuration import Configuration

from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import SearchMode
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

        self.clients = {}  # Cache SearchClient instances per index

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

    @retry(
        stop=stop_after_attempt(5)
    )
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
                    result = await resp.json(content_type=None)

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
        
    async def delete_documents(self, index_name: str, key_field: str, key_values: List[str]):
        """
        Deletes multiple documents from the specified Azure AI Search index.

        Parameters:
            index_name (str): The name of the Azure AI Search index.
            key_field (str): The name of the key field in the index.
            key_values (List[str]): A list of key values identifying the documents to delete.
        """
        if not key_values:
            logging.warning("[aisearch] No key values provided for deletion.")
            return

        client = await self.get_search_client(index_name)

        try:
            # Prepare the delete actions
            actions = [{"@search.action": "delete", key_field: key_value} for key_value in key_values]

            # Azure AI Search supports batch operations, but there might be limits on batch size.
            # Here, we assume that the list is within acceptable limits. For very large lists, consider batching.
            result = await client.upload_documents(documents=actions)

            # Check results
            succeeded = 0
            failed = 0
            for res in result:
                if res.succeeded:
                    succeeded += 1
                else:
                    failed += 1
                    error_messages = "; ".join([error["error"] for error in res.error_messages])
                    logging.error(f"[aisearch] Failed to delete a document: {error_messages}")

            logging.info(f"[aisearch] Deleted {succeeded} documents from '{index_name}'.")
            if failed > 0:
                logging.warning(f"[aisearch] Failed to delete {failed} documents from '{index_name}'. Check logs for details.")
        except AzureError as e:
            logging.error(f"[aisearch] AzureError while deleting documents from '{index_name}': {e}")
        except Exception as e:
            logging.error(f"[aisearch] Unexpected error while deleting documents from '{index_name}': {e}")

    async def get_search_client(self, index_name: str) -> SearchClient:
        """
        Retrieves a cached SearchClient for the specified index or creates a new one if not cached.

        Parameters:
            index_name (str): The name of the Azure AI Search index.

        Returns:
            SearchClient: An instance of SearchClient for the specified index.
        """
        if index_name not in self.clients:
            try:
                self.clients[index_name] = SearchClient(
                    endpoint=self.endpoint,
                    index_name=index_name,
                    credential=self.credential
                )
                logging.debug(f"[aisearch] Initialized SearchClient for index '{index_name}'.")
            except Exception as e:
                logging.error(f"[aisearch] Failed to initialize SearchClient for index '{index_name}': {e}")
                raise
        return self.clients[index_name]
    
    async def search_documents(
        self,
        index_name: str,
        search_text: str = "*",
        filter_field: Optional[str] = None,
        filter_value: Optional[Any] = None,
        filter_operator: str = "eq",
        select_fields: Optional[List[str]] = None,
        top: int = 10,
        skip: int = 0,
        order_by: Optional[str] = None,
        filter_str: Optional[str] = None  # <-- Add this
    ) -> Dict[str, Any]:
        client = await self.get_search_client(index_name)
        try:
            # Construct the filter string only if filter_str is not provided
            if filter_str is None and filter_field and filter_value is not None:
                if isinstance(filter_value, str):
                    escaped_value = filter_value.replace("'", "''")
                    filter_str = f"{filter_field} {filter_operator} '{escaped_value}'"
                else:
                    filter_str = f"{filter_field} {filter_operator} {filter_value}"

            search_kwargs = {
                "search_text": search_text,
                "filter": filter_str,
                "order_by": order_by,
                "search_mode": SearchMode.ALL,
                "skip": skip
            }

            if select_fields:
                search_kwargs["select"] = select_fields

            if top > 0:
                search_kwargs["top"] = top
            else:
                search_kwargs["top"] = 1000

            results = await client.search(**search_kwargs)
            documents = []
            async for result in results:
                documents.append(result)
                if top > 0 and len(documents) >= top:
                    break

            return {
                "count": len(documents),
                "documents": documents
            }

        except AzureError as e:
            logging.error(f"[aisearch] AzureError while searching documents in '{index_name}': {e}")
            return {"count": 0, "documents": [], "error": str(e)}
        except Exception as e:
            logging.error(f"[aisearch] Unexpected error while searching documents in '{index_name}': {e}")
            return {"count": 0, "documents": [], "error": str(e)}

    def call_search_api(self, search_service, search_api_version, resource_type, resource_name, method, credential, body=None):
        """
        Calls the Azure Search API with the specified parameters.
        """

        headers = {
            'Content-Type': 'application/json'
        }

        if self.api_key is not None:
            headers["API-KEY"] = self.api_key
        else:
            token = credential.get_token("https://search.azure.com/.default").token
            headers["Authorization"] = f"Bearer {token}"
        

        search_endpoint = f"https://{search_service}.search.windows.net/{resource_type}/{resource_name}?api-version={search_api_version}"
        response = None
        try:
            if method not in ["get", "put", "post", "delete"]:
                logging.warning(f"[call_search_api] Invalid method {method} ")

            if method == "get":
                response = requests.get(search_endpoint, headers=headers)
            elif method == "put":
                response = requests.put(search_endpoint, headers=headers, json=body)
            elif method == "post":
                response = requests.post(search_endpoint, headers=headers, json=body)
            if method == "delete":
                response = requests.delete(search_endpoint, headers=headers)
                status_code = response.status_code
                logging.info(f"[call_search_api] Successfully called search API {method} {resource_type} {resource_name}. Code: {status_code}.")

            if response is not None:
                status_code = response.status_code
                if status_code >= 400:
                    logging.warning(f"[call_search_api] {status_code} code when calling search API {method} {resource_type} {resource_name}. Reason: {response.reason}.")
                    try:
                        response_text_dict = json.loads(response.text)
                        logging.warning(f"[call_search_api] {status_code} code when calling search API {method} {resource_type} {resource_name}. Message: {response_text_dict['error']['message']}")        
                    except json.JSONDecodeError:
                        logging.warning(f"[call_search_api] {status_code} Response is not valid JSON. Raw response:\n{response.text}")
                else:
                    logging.info(f"[call_search_api] Successfully called search API {method} {resource_type} {resource_name}. Code: {status_code}.")
        except Exception as e:
            error_message = str(e)
            logging.error(f"Error when calling search API {method} {resource_type} {resource_name}. Error: {error_message}")

    def delete_item(self, index_name, item):
        body = self.create_item_body(item)
        return self.call_search_api(self.search_service, self.api_version, f"indexes", f"{index_name}/docs/index", "delete", self.config.credential, body)

    def create_item(self, index_name, item):
        body = self.create_item_body(item)
        return self.call_search_api(self.search_service, self.api_version, f"indexes", f"{index_name}/docs/index", "post", self.config.credential, body)

    def create_item_body(self, item:Dict={}, action="mergeOrUpload"):
        """
        Creates the body for the item to be added to the index.
        """

        if 'id' not in item:
            raise ValueError("Item must contain an 'id' field.")

        search_item = {
                    "@search.action": action,
                    "id": item["id"],
                    "content": item.get('content', None),
                    "metadata_storage_name": item.get("metadata_storage_name", None),
                    "metadata_storage_path": item.get("metadata_storage_path",None),
                    "metadata_storage_content_type": item.get("metadata_storage_content_type", None),
                    "contentVector": item.get("contentVector", None)
                }
    
        for field_name, field_value in item.items():
            if type(field_value) == pd.Timestamp:
                field_value = field_value.isoformat()
            if str(field_value) == 'nan':
                field_value = None
            search_item[field_name.replace(' ', '_')] = field_value

        body = {
            "value": [
                search_item
            ]
        }
        return body
    
    def create_datasource(self,search_service, search_api_version, datasource_name, storage_connection_string, container_name, credential, subfolder=None, identity=None):
        body = {
            "description": f"Datastore for {datasource_name}",
            "type": "azureblob",
            "dataDeletionDetectionPolicy": {
                "@odata.type": "#Microsoft.Azure.Search.NativeBlobSoftDeleteDeletionDetectionPolicy"
            },
            "credentials": {
                "connectionString": storage_connection_string
            },
            "container": {
                "name": container_name,
                "query": f"{subfolder}/" if subfolder else ""
            }
        }
        if identity:
            body["identity"] = {
                "@odata.type": "#Microsoft.Azure.Search.DataUserAssignedIdentity",
                "userAssignedIdentity": identity
            }

    def create_index_body(index_name, fields, content_fields_name, keyword_field_name, vector_profile_name="myHnswProfile", vector_algorithm_name="myHnswConfig"):
        body = {
            "name": index_name,
            "fields": fields,
            "corsOptions": {
                "allowedOrigins": ["*"],
                "maxAgeInSeconds": 60
            },
            "vectorSearch": {
                "profiles": [
                    {
                        "name": vector_profile_name,
                        "algorithm": vector_algorithm_name
                    }
                ],
                "algorithms": [
                    {
                        "name": vector_algorithm_name,
                        "kind": "hnsw",
                        "hnswParameters": {
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    }
                ]
            },
            "semantic": {
                "configurations": [
                    {
                        "name": "my-semantic-config",
                        "prioritizedFields": {
                            "prioritizedContentFields": [
                                {
                                    "fieldName": field_name
                                }
                                for field_name in content_fields_name
                            ]
                        }
                    }
                ]
            }
        }
        if keyword_field_name is not None:
            body["semantic"]["configurations"][0]["prioritizedFields"]["prioritizedKeywordsFields"] = [
                {
                    "fieldName": keyword_field_name
                }
            ]
        return body
    
    def create_indexer_body(indexer_name, index_name, data_source_name, skillset_name, field_mappings=None, indexing_parameters=None):
        body = {
            "name": indexer_name,
            "dataSourceName": data_source_name,
            "targetIndexName": index_name,
            "skillsetName": skillset_name,
            "schedule": {
                "interval": "PT2H"
            },
            "fieldMappings": field_mappings if field_mappings else [],
            "outputFieldMappings": [
                {
                    "sourceFieldName": "/document/contentVector",
                    "targetFieldName": "contentVector"
                }
            ],
            "parameters":
            {
                "configuration": {
                    "parsingMode": "json"
                }
            }            
        }
        if indexing_parameters:
            body["parameters"] = indexing_parameters
        return body

    def create_embedding_skillset(skillset_name, resource_uri, deployment_id, model_name, input_field, output_field, dimensions):
        skill = {
            "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
            "name": f"{skillset_name}-embedding-skill",
            "description": f"Generates embeddings for {input_field}.",
            "resourceUri": resource_uri,
            "deploymentId": deployment_id,
            "modelName": model_name,
            "dimensions": dimensions,
            "context":"/document",            
            "inputs": [
                {
                    "name": "text",
                    "source": f"/document/{input_field}"
                }
            ],
            "outputs": [
                {
                    "name": "embedding",
                    "targetName": output_field
                }
            ]
        }
        skillset_body = {
            "name": skillset_name,
            "description": f"Skillset for generating embeddings for {skillset_name} index.",
            "skills": [skill]
        }
        return skillset_body