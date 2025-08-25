import os
import logging
from azure.identity import DefaultAzureCredential, ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential, ChainedTokenCredential as AsyncChainedTokenCredential, ManagedIdentityCredential as AsyncManagedIdentityCredential, AzureCliCredential as AsyncAzureCliCredential
from azure.appconfiguration.provider import (
    AzureAppConfigurationKeyVaultOptions,
    load,
    SettingSelector
)

from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError

class Configuration:

    credential = None
    aiocredential = None

    def retry_before_sleep(self, retry_state):
        # Log the outcome of each retry attempt.
        message = f"""Retrying {retry_state.fn}:
                        attempt {retry_state.attempt_number}
                        ended with: {retry_state.outcome}"""
        if retry_state.outcome.failed:
            ex = retry_state.outcome.exception()
            message += f"; Exception: {ex.__class__.__name__}: {ex}"
        if retry_state.attempt_number < 1:
            logging.info(message)
        else:
            logging.warning(message)

    def __init__(self):

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
        
        self._init_clients()

    @retry(
        stop=stop_after_attempt(5)
    )
    def _init_clients(self):
        no_label_selector = SettingSelector(label_filter=None, key_filter='*')
        label_selector = SettingSelector(label_filter='gpt-rag', key_filter='*')
        
        try:
            app_config_uri = os.environ['APP_CONFIGURATION_URI'] #backward compatibility
        except Exception as e:
            app_config_uri = os.environ['APP_CONFIG_ENDPOINT']

        try:
            self.config = load(selects=[no_label_selector, label_selector],endpoint=app_config_uri, credential=self.credential,key_vault_options=AzureAppConfigurationKeyVaultOptions(credential=self.credential))
        except Exception as e:
            logging.info(f"Unable to connect to Azure App Configuration. Please check app config url setting. {e}")
            try:
                connection_string = os.environ["AZURE_APPCONFIG_CONNECTION_STRING"]
                # Connect to Azure App Configuration using a connection string.
                self.config = load(connection_string=connection_string, key_vault_options=AzureAppConfigurationKeyVaultOptions(credential=self.credential))
            except Exception as e:
                raise Exception(f"Unable to connect to Azure App Configuration. Please check your connection string or endpoint. {e}")

    
    # Connect to Azure App Configuration.
    def get(self, key: str, default: str = None, allow_none: bool = False, type: type = str) -> str:
        return self.get_value(key=key, default=default, allow_none=allow_none, type=type)

    def get_value(self, key: str, default: str = None, allow_none: bool = False, type: type = str) -> str:

        if key is None:
            raise Exception('The key parameter is required for get_value().')

        value = None

        allow_env_vars = False
        if "allow_environment_variables" in os.environ:
            allow_env_vars = bool(os.environ[
                    "allow_environment_variables"
                    ])

        if allow_env_vars is True:
            value = os.environ.get(key)

        if value is None:
            try:
                value = self.get_config_with_retry(name=key)
            except Exception as e:
                pass

        if value is not None:
            if type is not None:
                if type is bool:
                    if isinstance(value, str):
                        value = value.lower() in ['true', '1', 'yes']
                else:
                    try:
                        value = type(value)
                    except ValueError as e:
                        raise Exception(f'Value for {key} could not be converted to {type.__name__}. Error: {e}')
            return value
        else:
            if default is not None or allow_none is True:
                return default
            
            raise Exception(f'The configuration variable {key} not found.')

    @retry(
        wait=wait_random_exponential(multiplier=1, max=5),
        stop=stop_after_attempt(5),
        before_sleep=retry_before_sleep
    )
    def get_config_with_retry(self, name):
        try:
            return self.config[name]
        except RetryError:
            pass

    # Helper functions for reading environment variables
    def read_env_variable(self, var_name, default=None):
        value = self.get_value(var_name, default)
        return value.strip() if value else default

    def read_env_list(self, var_name):
        value = self.get_value(var_name, "")
        return [item.strip() for item in value.split(",") if item.strip()]

    def read_env_boolean(self, var_name, default=False):
        value = self.get_value(var_name, str(default)).strip().lower()
        return value in ['true', '1', 'yes']