from pydantic import BaseModel, Field
from typing import Optional

class ContentIdentifier(BaseModel):

    canonical_id : str = Field(default=..., description='Canonical identifier for the content')
    unique_id : Optional[str] = Field(default=None, description='Unique identifier for the content')
    source_id : str = Field(default=..., description='Identifier for the source instance of the content')
    source_name : Optional[str] = Field(default=None, description='Name of the source instance of the content')
    source_type : Optional[str] = Field(default=None, description='Type of the data source (e.g., azure_blob, azure_files, sharepoint)')
    container : Optional[str] = Field(default=None, description='Container or bucket name where the content is stored')
    path : Optional[str] = Field(default=None, description='Path or location of the content within the source')
    metadata : dict[str, object] | None = Field(default=None, description='Metadata associated with the content')