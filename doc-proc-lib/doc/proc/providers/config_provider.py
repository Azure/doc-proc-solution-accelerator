import os
import logging

from azure.identity import ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential
from azure.identity.aio import ChainedTokenCredential as AsyncChainedTokenCredential, ManagedIdentityCredential as AsyncManagedIdentityCredential, AzureCliCredential as AsyncAzureCliCredential
from azure.appconfiguration.provider import (
    AzureAppConfigurationKeyVaultOptions,
    load,
    SettingSelector,
    WatchKey
)

from doc.proc.providers.credential_provider import get_azure_credential

class ConfigurationProvider:

    def __init__(self, config_key_filters: list[str] = []):
        self.app_config_endpoint = os.environ.get("AZURE_APP_CONFIG_ENDPOINT", None)

        print(f"Attempting to load configuration from Azure App Configuration with endpoint: {self.app_config_endpoint}")

        if not self.app_config_endpoint:
            raise Exception("AZURE_APP_CONFIG_ENDPOINT environment variable is not set.")

        _key_filters = ["doc-proc.common.*", *config_key_filters]

        _selects = [SettingSelector(key_filter=key_filter) for key_filter in _key_filters]
        _credential = get_azure_credential()
        
        self.config = load(
            endpoint=self.app_config_endpoint,
            selects=_selects,
            credential=_credential,
            key_vault_options=AzureAppConfigurationKeyVaultOptions(credential=_credential),
            trim_prefixes=[ kf.replace('*', '') for kf in _key_filters ],
            refresh_on=[WatchKey("sentinel")],
            refresh_interval=60 * 5,  # Check for refresh every 5 minutes
            on_refresh_success=self._on_refresh,
            feature_flag_enabled=True,
            feature_flag_refresh_enabled=True,
        )

        print(f"Initialized ConfigurationProvider with endpoint: {self.app_config_endpoint}")
        print(f"Initial configuration keys: {list(self.config.keys())}")

        self._on_refresh_callbacks = []

    def request_refresh(self):
        if self.config:
            self.config.refresh()

    def _on_refresh(self):
        for callback in self._on_refresh_callbacks:
            try:
                callback()
            except Exception as e:
                logging.error(f"Error executing refresh callback: {e}")


    def add_on_refresh_callback(self, callback):
        self._on_refresh_callbacks.append(callback)


    def get_config_value(self, key: str, default: str = None, allow_none: bool = True, allow_env_vars: bool = True, type: type = str):
        if key in ['', None]:
            raise ValueError('The key parameter is required.')

        try:
            value = self.config.get(key=key, default='').strip()
        except Exception as e:
            pass

        if value not in [None, '']:
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
        elif allow_env_vars and os.getenv(key) is not None:
            value = os.getenv(key).strip()
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
            
        raise KeyError(f'The configuration key {key} not found.')