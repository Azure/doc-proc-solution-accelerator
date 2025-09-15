from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class BaseDoc(BaseModel):
    id: str = Field(..., description="Unique id, used as partition key")
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self):
        self.updated_at = datetime.now(timezone.utc)
        return self
