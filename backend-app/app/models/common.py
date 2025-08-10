from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseDoc(BaseModel):
    id: str = Field(..., description="Unique id, used as partition key")
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def touch(self):
        self.updated_at = datetime.utcnow()
        return self
