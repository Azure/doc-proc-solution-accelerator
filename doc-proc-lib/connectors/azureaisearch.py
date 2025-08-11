import logging
import json
import requests
import pandas as pd

from datetime import datetime as Timestamp
from typing import Dict
from configuration import Configuration

class AzureAISearch:
    """
    """
    def __init__(self, config:Configuration=None):
        if (config is None):
            self.config = Configuration()
        else:
            self.config = config

        self.search_service = self.config.get_value("AZURE_SEARCH_SERVICE")
        self.search_index = self.config.get_value("AZURE_SEARCH_INDEX_NAME")
        self.search_api_version = self.config.get_value("AZURE_SEARCH_API_VERSION", "2024-07-01")
        self.search_api_key = self.config.get_value("AZURE_SEARCH_APIKEY", None, allow_none=True)
        # Build the search endpoint URL.
        self.search_endpoint = (
            f"https://{self.search_service}.search.windows.net/indexes/{self.search_index}/docs/search?api-version={self.search_api_version}"
        )

    def call_search_api(self, search_service, search_api_version, resource_type, resource_name, method, credential, body=None):
        """
        Calls the Azure Search API with the specified parameters.
        """

        headers = {
            'Content-Type': 'application/json'
        }

        if self.search_api_key is not None:
            headers["API-KEY"] = self.search_api_key
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

    def create_item(self, index_name, item):
        body = self.create_item_body(item)
        return self.call_search_api(self.search_service, self.search_api_version, f"indexes", f"{index_name}/docs/index", "post", self.config.credential, body)

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