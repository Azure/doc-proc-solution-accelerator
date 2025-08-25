import logging
import os
import tiktoken

from typing import List
from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError

from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, ChatRequestMessage, ChatCompletions

from doc.proc.service.service_base import ServiceBase, ServiceExecutionError

logger = logging.getLogger("doc.proc.service.azure_ai_inference_service") # need to specify the logger name as this module is loaded dynamically

class AzureAIInferenceService(ServiceBase):
    """Azure AI Inference service for managing AI inference operations."""

    def __init__(self, name: str, type: str, settings:dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.endpoint = settings.get('endpoint', '').strip()
        self.credential_type = settings.get('credential_type', '').strip()
        self.model_name = settings.get('model_name', '').strip()
        self.api_key = ''

        self.model = self._get_model(self.model_name)

        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Validate endpoint
        if not self.endpoint:
            raise ValueError("Settings key 'endpoint' is required")

        if self.endpoint.startswith('${') and self.endpoint.endswith('}'):
            env_var_name = self.endpoint[2:-1]
            self.endpoint = self.config.get(env_var_name)

            if (self.model_name):
                self.endpoint = f"{self.endpoint}/openai/deployments/{self.model_name}"

            if not self.endpoint:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            self.endpoint = self.endpoint


        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        if self.credential_type.startswith('${') and self.credential_type.endswith('}'):
            env_var_name = self.credential_type[2:-1]
            self.credential_type = self.config.get(env_var_name)
            if not self.credential_type:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        else:
            self.credential_type = self.credential_type
            #raise ValueError("Settings key 'credential_type' must be in the format '${ENV_VAR_NAME}' and be present as an environment variable")


        # Validate API key based on credential type
        if self.credential_type == 'azure_key_credential':
            self.api_key = settings.get('api_key', '').strip()

            if not self.api_key:
                raise ValueError("Settings key 'api_key' is required for azure_key_credential")

            # Read the API key from environment variable
            if self.api_key.startswith('${') and self.api_key.endswith('}'):
                env_var_name = self.api_key[2:-1]
                self.api_key = self.config.get(env_var_name)
                if not self.api_key:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            else:
                self.api_key = self.api_key

        elif self.credential_type == 'default_azure_credential':
            self.api_key = ''        
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}. Supported types are 'azure_key_credential' and 'default_azure_credential'.")

        self.chat_completions_client: ChatCompletionsClient = None
        self.__init_client()


    @retry(
        stop=stop_after_attempt(5)
    )
    def __init_client(self):
        """Initialize the ChatCompletionsClient."""

        logger.debug(f"Creating ChatCompletionsClient with endpoint: {self.endpoint} and credential type: {self.credential_type}")

        if self.api_key not in ['', None]:
            self.chat_completions_client = ChatCompletionsClient(endpoint=self.endpoint, 
                                                                 credential=AzureKeyCredential(self.api_key))
        else:
            self._get_credentials()
            self.chat_completions_client = ChatCompletionsClient(endpoint=self.endpoint, 
                                                                 credential=self.credential, 
                                                                 credential_scopes=["https://cognitiveservices.azure.com/.default"])

        logger.debug(f"Initialized ChatCompletionsClient for Azure AI Inference Service: {self.name}")


    async def test_connection(self) -> bool:
        """Test the connection to the Azure Blob Storage service."""
        try:
            
            # Attempt to get model info to verify connection
            response = self.chat_completions_client.complete(messages=[
                SystemMessage("Reply with YES")
            ])

            logger.debug(f"Connected to Azure AI Inference Service: {self.name}")

            # If we reach here, the connection is successful
            return response is not None
        except Exception as e:
            raise ServiceExecutionError(f"Failed to connect to Azure AI Inference Service: {str(e)}")


    def run_chat_completion(self, messages: List[ChatRequestMessage],
                                   max_completion_tokens: int,
                                   temperature: float,
                                   top_p: float,
                                   frequency_penalty: float,
                                   presence_penalty: float,
                                   response_format: str = None) -> ChatCompletions:
        """Run chat completion using the Azure AI Inference Service."""
        try:
            response = self.chat_completions_client.complete(
                                                            messages=messages,
                                                            max_tokens=max_completion_tokens,
                                                            temperature=temperature,
                                                            top_p=top_p,
                                                            frequency_penalty=frequency_penalty,
                                                            presence_penalty=presence_penalty,
                                                            response_format=response_format
                                                        )
            return response
        except Exception as e:
            logger.error(f"Error occurred while running chat completion: {str(e)}")
            raise ServiceExecutionError(f"Failed to run chat completion: {str(e)}")