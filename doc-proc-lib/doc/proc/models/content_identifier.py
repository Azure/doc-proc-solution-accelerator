from pydantic import BaseModel, Field
from typing import Optional

class ContentIdentifier(BaseModel):

    data_source_object_id : str = None
    unique_id : Optional[str] = ''
    multipart_id : list[str] = None
    canonical_id : str
    metadata : dict[str, object] | None = None