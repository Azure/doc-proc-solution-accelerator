import enum
import pydantic

from pydantic import BaseModel
from typing import Any, Optional

class DocProcArtifactType(str, enum.Enum):
    ExtractedText = "extracted_text"
    ExtractedMetadata = "extracted_metadata"
    ExtractedSecurity = "extracted_security"
    TextPartition = "text_partition"
    TextEmbeddingVector = "text_embedding_vector"

class DocProcArtifact(BaseModel):
    type : DocProcArtifactType
    canonical_id : str = None
    position : int = 0
    size : int = 0
    data : Optional[str] = None
    content_hash : Optional[str] = None
    is_dirty : bool = False