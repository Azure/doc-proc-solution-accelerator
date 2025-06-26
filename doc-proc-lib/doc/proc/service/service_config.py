from pydantic import BaseModel
from typing import List, Optional
import yaml

class ServiceConfig(BaseModel):
    """Represents a service used in the system."""
    name: str
    type: str  # Type of service, e.g., "azure_blob", "azure_search", etc.
    test_connection: bool = True
    settings: dict = {}

    @staticmethod
    def from_dict(config: dict) -> "ServiceConfig":
        return ServiceConfig(**config)

    @staticmethod
    def from_yaml(yaml_str: str) -> List["ServiceConfig"]:
        """Load services configuration from a YAML string."""
        if not yaml_str:
            raise ValueError("YAML string cannot be empty")
        try:
            config = yaml.safe_load(yaml_str)
            services = config.get("services", [])
            return [ServiceConfig.from_dict(s) for s in services]
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValueError(f"An error occurred while loading the service configuration: {str(e)}")
