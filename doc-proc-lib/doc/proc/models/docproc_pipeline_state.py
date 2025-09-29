from typing import Optional, List
from datetime import datetime

from doc.proc.models.docproc_processing_state import DocProcProcessingState

class DocProcPipelineState:
    id : str
    pipeline_object_id : str
    execution_start : Optional[datetime]
    execution_end : Optional[datetime]
    docproc_request_object_ids : List[str] = []
    processing_state : DocProcProcessingState = DocProcProcessingState.NEW
    error_messages : List[str] = [] 