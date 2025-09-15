from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class BaseDoc(BaseModel):
    id: str = Field(..., description="Unique id, used as partition key")
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Created time in utc tz iso-format")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Updated time in utc tz iso-format")

    def touch(self):
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return self
