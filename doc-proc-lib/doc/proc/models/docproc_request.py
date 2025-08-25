import uuid

from .content_identifier import ContentIdentifier
from .docproc_processing_type import DocProcProcessingType
from .docproc_processing_state import DocProcProcessingState
from .docproc_step import DocProcStep
from .docproc_long_running_operation import DocProcLongRunningOperation

from typing import List, Dict, Union
from datetime import datetime, timezone

from pydantic import BaseModel, Field

class DocProcRequest(BaseModel, use_enum_values=True):

        content_identifier : ContentIdentifier

        processing_type : DocProcProcessingType

        pipeline_object_id : str
        
        pipeline_name : str

        pipeline_execution_id : str = str(uuid.uuid4())

        processing_state : DocProcProcessingState = DocProcProcessingState.NEW

        execution_start : datetime = None

        execution_end : datetime = None

        error_messages : list[str] = []

        steps : list[DocProcStep] = []

        completed_steps : list[str] = []

        remaining_steps : list[str] = []

        current_step : str | None = None
        
        if remaining_steps:
            current_step = remaining_steps[0]

        error_count : int = 0

        running_operations : dict[str, DocProcLongRunningOperation] = {}

        last_successful_step_time : datetime = datetime.now(timezone.utc)

        complete : bool = remaining_steps.count == 0