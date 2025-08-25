from pydantic import BaseModel, Field

class DocProcStep(BaseModel):

    id : str
    parameters : dict[str, str]