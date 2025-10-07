from pydantic import BaseModel, Field
from typing import List, Optional

from doc.proc.models.content_identifier import ContentIdentifier


class Document(BaseModel):
    """Input/Output data structure for pipeline steps that holds document data."""
    
    id: ContentIdentifier = Field(default=None, description="Content identifier for the document")
    summary_data: dict = Field(default_factory=dict, description="Summary data for the document")
    data: dict = Field(default_factory=dict, description="Main data dictionary for the document")