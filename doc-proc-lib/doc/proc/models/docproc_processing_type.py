
import enum

from pydantic import BaseModel, Field

class DocProcProcessingType(enum.Enum):
    """ Represents the type of processing to be performed. """
    asynchronous = "asynchronous"
    synchronous = "synchronous"