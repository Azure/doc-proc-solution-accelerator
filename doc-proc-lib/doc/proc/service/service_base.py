import os
import logging
import json

from typing import Dict, List
from abc import abstractmethod
from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential
from azure.identity.aio import AzureCliCredential as AsyncAzureCliCredential, ChainedTokenCredential as AsyncChainedTokenCredential, ManagedIdentityCredential as AsyncManagedIdentityCredential

class ServiceExecutionError(Exception):
    """Custom exception for errors during service execution."""
    pass


class ServiceBase:
    """
    Base class for services.
    This class provides a method to get an instance of a service based on the provided settings.
    """

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        self.name = name
        self.type = type
        self.settings = settings or {}
        self.params = kwargs

        from dependencies import get_config
        self.config = get_config()

        if not self.name:
            raise ValueError("Service name cannot be empty")
        
        if not self.type:
            raise ValueError("Service type cannot be empty")
        
        self.settings = self._parse_settings(self.settings)

    def _parse_settings(self, settings: Dict) -> Dict:
        """Parse environment variables in the given settings dictionary."""
        parsed_settings = {}
        for key, value in settings.items():
            parsed_settings[key] = self._parse_env(value)
        return parsed_settings
     
    def _parse_env(self, value: str) -> str:
        """Parse environment variables in the given value."""
        if not value:
            return value
        
        if isinstance(value, str) and value.startswith("$"):
            env_var = value[1:].replace("{", "").replace("}", "")
            value = self.config.get(env_var, value)
        
            if not value:
                raise ValueError(f"Environment variable '{env_var}' is not set or empty. Ensure it is defined in your environment or .env file.")

        return value
    
    def _get_credentials(self):
        try:
            self.tenant_id = os.environ.get('AZURE_TENANT_ID', "*")
        except Exception as e:
            raise e
        
        try:
            self.client_id = os.environ.get('AZURE_CLIENT_ID', "*")
        except Exception as e:
            raise e
        
        self.credential = ChainedTokenCredential(
                ManagedIdentityCredential(client_id=self.client_id),
                AzureCliCredential()
            )
        
        self.aiocredential = AsyncChainedTokenCredential(
                AsyncManagedIdentityCredential(client_id=self.client_id),
                AsyncAzureCliCredential()
            )
        
    def _get_model(self, model_name: str = 'CHAT_DEPLOYMENT_NAME') -> Dict:
        model_deployments = self.config.get_value("MODEL_DEPLOYMENTS", default='[]').replace("'", "\"")

        try:
            print(f"Model deployments: {model_deployments}")
            logging.info(f"Model deployments: {model_deployments}")

            json_model_deployments = json.loads(model_deployments)

            #get the canonical_name of 'CHAT_DEPLOYMENT_NAME'
            for deployment in json_model_deployments:
                if deployment.get("canonical_name") == model_name:
                    return deployment
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON for model deployments: {e}")
            raise ValueError(f"Invalid model deployments configuration: {model_deployments}")
            
        return None

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the service connection.
        This method should be overridden by subclasses to implement specific service tests.
        """
        raise NotImplementedError("Subclasses must implement this method.")