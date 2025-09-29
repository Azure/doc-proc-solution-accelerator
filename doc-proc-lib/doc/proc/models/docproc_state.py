import uuid
import pydantic

from pydantic import BaseModel, ConfigDict, model_serializer, SerializerFunctionWrapHandler, FieldSerializationInfo

from doc.proc.models.docproc_artifact import DocProcArtifact, DocProcArtifactType
from doc.proc.models.docproc_index_reference import DocProcIndexReference
from doc.proc.models.docproc_log_entry import DocProcLogEntry
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.step.step_base import StepBase

from typing import List

class DocProcStateItem(BaseModel):
    pipeline_name: str
    position: int
    text_partition_content: str
    text_partition_hash: str
    text_partition_size: int
    text_embedding_vector_size: int
    text_embedding_vector: List[float]
    text_embedding_vector_hash: str
    text_partition_hash: str
    text_partition_size: int
    text_embedding_vector_size: int
    text_embedding_vector: List[float]
    text_embedding_vector_hash: str

class DocProcState(BaseModel):

    request_id : str = str(uuid.uuid4())

    content_identifier : ContentIdentifier = None

    artifacts : List[DocProcArtifact] = []

    index_references : List[DocProcIndexReference] = []
        
    pipeline_name : str = None

    pipeline_object_id : str = None

    request : DocProcRequest = None

    log : List[DocProcLogEntry] = []

    loaded_artifact_types: List[DocProcArtifactType] = []

    def add_log_entry(self, handler: StepBase, request_id: str, message_id: str, text: str):
        self.log.append(DocProcLogEntry(
            request_id=request_id,
            message_id=message_id,
            step_id=handler.name,
            text=text
        ))

    def log_handler_start(self, handler: StepBase, request_id: str, message_id: str):
        self.log.append(DocProcLogEntry(
            request_id=request_id,
            message_id=message_id,
            step_id=handler.name,
            text="Started handling step."
        ))

    def log_handler_end(self, handler: StepBase, request_id: str, message_id: str):
        self.log.append(DocProcLogEntry(
            request_id=request_id,
            message_id=message_id,
            step_id=handler.name,
            text="Finished handling step."
        ))