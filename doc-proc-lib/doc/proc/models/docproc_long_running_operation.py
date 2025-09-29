from datetime import datetime

from pydantic import BaseModel, Field

class DocProcLongRunningOperation(BaseModel):

    operation_id : str

    first_response_time : datetime

    last_response_time : datetime

    complete : bool

    polling_count : int