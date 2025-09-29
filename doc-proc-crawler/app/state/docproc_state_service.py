import hashlib

from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState
from doc.proc.models.content_identifier import ContentIdentifier

class DocProcStateService:

    def get_persistence_identifier(self, docProcRequest : DocProcRequest):
        return f"{docProcRequest.content_identifier.data_source_object_id}/{docProcRequest.content_identifier.canonical_id}_state_{self.hash_content_identifier(docProcRequest.content_identifier)}"

    def get_persistence_identifier(self, docProcState : DocProcState):
        return f"{docProcState.content_identifier.data_source_object_id}/{docProcState.content_identifier.canonical_id}_state_{self.hash_content_identifier(docProcState.content_identifier)}"

    def hash_content_identifier(self, contentIdentifier : ContentIdentifier):        
        if (contentIdentifier.unique_id == None):
            contentIdentifier.unique_id = ''
            
        byteHash = hashlib.md5(
            (contentIdentifier.canonical_id + "|" + contentIdentifier.unique_id).encode("utf-8")
        ).digest()

        return byteHash.hex()

    def hash_text(self, text : str):
        byteHash = hashlib.md5(
            text.encode("utf-8")
        ).digest()

        return byteHash.hex()
    
    async def has_state(self, request: DocProcRequest) -> bool:
        raise NotImplementedError
    
    async def get_state(self, request: DocProcRequest) -> bool:
        raise NotImplementedError
    
    async def save_state(self, state: DocProcState) -> bool:
        raise NotImplementedError
    
    async def delete_state(self, state: DocProcState) -> bool:
        raise NotImplementedError
    
    def get_source_items(self, source):
        raise NotImplementedError