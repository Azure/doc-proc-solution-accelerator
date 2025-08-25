import pydantic

from pydantic import BaseModel

class DocProcIndexReference(BaseModel):
    index_entry_id : str    
    position : int