from pydantic import BaseModel, RootModel
from typing import List, Optional
import yaml

class ConfigSchemaSettings(RootModel[dict[str, "ConfigSchemaParameter"]]):
    """Generic settings for service configuration."""

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value

    def dict(self, **kwargs):
        return self.root