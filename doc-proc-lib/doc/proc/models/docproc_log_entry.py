import pydantic

from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone

class DocProcLogEntry(BaseModel):   
    request_id : Optional[str]
    message_id : Optional[str]
    time : Optional[datetime] = datetime.now(timezone.utc)
    step_id : Optional[str]
    text : str = None