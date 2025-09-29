import logging
import os
import tiktoken

from typing import List
from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError

from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import EmbeddingsClient
from azure.ai.inference.models import SystemMessage, ChatRequestMessage, ChatCompletions

from doc.proc.service.service_base import ServiceBase, ServiceExecutionError

logger = logging.getLogger("doc.proc.service.azure_ai_embedding_service") # need to specify the logger name as this module is loaded dynamically

class AzureAIEmbeddingService(ServiceBase):
    """Azure AI Embedding service for managing AI embedding operations."""

    def __init__(self, name: str, type: str, settings:dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.endpoint = self.settings.get('endpoint', '').strip()
        self.credential_type = self.settings.get('credential_type', '').strip()
        self.model_name = self.settings.get('model_name', '').strip()
        self.api_key = ''
        self.max_tokens = self.settings.get('max_tokens', 8192)

        self.model = self._get_model(self.model_name)
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Validate endpoint
        if not self.endpoint:
            raise ValueError("Settings key 'endpoint' is required")

        self.endpoint = self.endpoint

        if self.model_name:
            self.endpoint = self.endpoint.rstrip('/') + "/openai/deployments/" + self.model_name    

        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        self.credential_type = self.credential_type

        # Validate API key based on credential type
        if self.credential_type == 'azure_key_credential':
            self.api_key = self.settings.get('api_key', '').strip()

            if not self.api_key:
                raise ValueError("Settings key 'api_key' is required for azure_key_credential")

            self.api_key = self.api_key

        elif self.credential_type == 'default_azure_credential':
            self.api_key = ''        
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}. Supported types are 'azure_key_credential' and 'default_azure_credential'.")

        self.embeddings_client: EmbeddingsClient = None
        self.__init_client()

    @retry(
        stop=stop_after_attempt(5)
    )
    def __init_client(self):
        """Initialize the EmbeddingsClient."""

        logger.debug(f"Creating EmbeddingsClient with endpoint: {self.endpoint} and credential type: {self.credential_type}")

        if self.api_key not in ['', None]:
            self.embeddings_client = EmbeddingsClient(endpoint=self.endpoint, 
                                                      credential=AzureKeyCredential(self.api_key))
        else:
            self._get_credentials()
            self.embeddings_client = EmbeddingsClient(endpoint=self.endpoint, 
                                                      credential=self.credential, 
                                                      credential_scopes=["https://cognitiveservices.azure.com/.default"])

        logger.debug(f"Initialized EmbeddingsClient for Azure AI Embedding Service: {self.name}")

    async def test_connection(self) -> bool:
        """Test the connection to the Azure Blob Storage service."""
        try:
            
            # Attempt to get model info to verify connection
            response = self.embeddings_client.embed(input="test")

            logger.debug(f"Connected to Azure AI Embedding Service: {self.name}")

            # If we reach here, the connection is successful
            return response is not None
        except Exception as e:
            raise ServiceExecutionError(f"Failed to connect to Azure AI Embedding Service: {str(e)}")

    def run_embeddings(self, content :str) -> ChatCompletions:
        """Run embeddings using the Azure AI Embedding Service."""
        try:
            tokens = self.encoding.encode(content)
            if len(tokens) > self.max_tokens:
                content = self.encoding.decode(tokens[:self.max_tokens])

            response = self.embeddings_client.embed(input=content)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error occurred while running embeddings: {str(e)}")
            raise ServiceExecutionError(f"Failed to run embeddings: {str(e)}")