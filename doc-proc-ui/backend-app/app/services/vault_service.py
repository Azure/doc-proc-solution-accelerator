import logging
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone

from fastapi import UploadFile

from app.db.cosmos import CosmosDb
from app.models.vault import (
    AddDocumentRequest, Vault, VaultCreateRequest, VaultUpdateRequest, VaultProcessingRequest,
    VaultStatus, VaultStats, DocumentInfo
)
from app.services.base import BaseService
from app.services.vault_documents_service import VaultDocumentsService

logger = logging.getLogger("doc-proc-ui.app.services.vault_service")

class VaultService(BaseService):
    """Service for managing document vaults"""

    def __init__(self, db: CosmosDb, 
                       container_name: str = "vaults", 
                       vault_documents_service: VaultDocumentsService = None,
                       default_blob_storage: Optional[Dict[str, Any]] = None):
        """
        Initialize VaultService with database connection and configuration.
        Args:
            db (CosmosDb): The Cosmos database instance for data persistence.
            container_name (str, optional): The name of the container to use for vault storage. 
                Defaults to "vaults".
            default_blob_storage (Optional[Dict[str, Any]], optional): Default blob storage 
                configuration details. Defaults to None, which initializes as empty dict.
                Example:
                {
                    "account_name": "your_account_name",
                    "container_name": "your_container_name",
                }
        Note:
            This service inherits from a parent class and manages vault-related operations
            with optional blob storage integration.
        """
        """Initialize VaultService"""
        
        super().__init__(db, container_name)
        
        self.vault_document_service = vault_documents_service
        self._default_storage_account_details = default_blob_storage or {}
        
        
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate vault item"""
        required_fields = ["id", "name", "storage_config"]
        return all(field in item for field in required_fields)


    async def create_vault(self, request: VaultCreateRequest) -> Vault:
        """Create a new vault"""
        
        # check if a vault with the same name already exists
        existing_vaults = await self.query(
            query="SELECT * FROM c WHERE c.name = @name",
            parameters=[{"name": "@name", "value": request.name}]
        )
        
        if existing_vaults and existing_vaults[0]:
            raise ValueError(f"A vault with the name '{request.name}' already exists.")
        
        # generate a unique ID for the vault
        vault_id = f"{request.name.replace(' ', '-')}_{uuid.uuid4().hex[:8]}"
        
        vault = Vault(
            id=vault_id,
            name=request.name,
            description=request.description,
            pipeline_name=request.pipeline_name,
            processing_config=request.processing_config or Vault.model_fields['processing_config'].default_factory(),
            storage_config=request.storage_config or self._get_default_vault_storage_config(),
            stats=VaultStats()
        )
        
        saved_vault = await self.create(vault.model_dump())
        return Vault(**saved_vault)


    def _get_default_vault_storage_config(self) -> Dict[str, Any]:
        """Get default storage configuration for a vault"""
        
        if not self._default_storage_account_details or not self._default_storage_account_details.get("account_name"):
            raise ValueError("Default storage account details are not configured")
                       
        return {
            "account_name": self._default_storage_account_details.get("account_name"),
            "container_name": self._default_storage_account_details.get("container_name", "vaults"),
            "credential_type": "default_azure_credential"
        }
        

    async def get_vault(self, vault_id: str) -> Optional[Vault]:
        """Get vault by ID"""
        vault_data = await self.get_by_id(vault_id)
        return Vault(**vault_data) if vault_data else None


    async def update_vault(self, vault_id: str, request: VaultUpdateRequest) -> Optional[Vault]:
        """Update a vault"""
        vault = await self.get_vault(vault_id)
        if not vault:
            return None

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(vault, field) and value is not None:
                setattr(vault, field, value)
        
        # Touch the updated_at field
        vault.touch()
        
        updated_vault = await self.update(vault_id, vault.model_dump())
        return Vault(**updated_vault)

    async def delete_vault(self, vault_id: str) -> bool:
        """Delete a vault"""
        return await self.delete(vault_id)

    async def list_vaults(self) -> List[Vault]:
        """List vaults"""
        
        items = await self.list_all()
        return [Vault(**item) for item in items]


    async def update_vault_stats(self, vault_id: str, stats: VaultStats) -> Optional[Vault]:
        """Update vault statistics"""
        vault = await self.get_vault(vault_id)
        if not vault:
            return None

        vault.stats = stats
        vault.touch()
        
        updated_vault = await self.update(vault_id, vault.model_dump())
        return Vault(**updated_vault)


    async def add_uploaded_documents(self, vault_id: str, files: List[UploadFile], overwrite: bool=False) -> List[DocumentInfo | Dict[str, Any]]:
        """Add a document to a vault (updates stats)"""
        vault = await self.get_vault(vault_id)
        if not vault:
            raise ValueError(f"Vault {vault_id} not found")

        if not files or not all(file.file for file in files):
            raise ValueError("File upload must be provided")

        _documents_uploaded = []
        _documents_failed = []
        _queued_docs = []
        for file in files:
            try:
                file_name_to_upload = file.filename
                file_contents = await file.read()
                file_content_type = file.content_type

                document_info = await self.vault_document_service.add_file(vault, file_name_to_upload, file_contents, file_content_type, overwrite=overwrite)
                _documents_uploaded.append(document_info)
            except Exception as e:
                logger.warning(f"Failed to upload file '{file.filename}' to vault '{vault_id}': {e}")
                _documents_failed.append({
                    "name": file.filename,
                    "error": str(e)
                })
                continue

        if _documents_uploaded and len(_documents_uploaded) > 0:
            # add a message to the queue to process the document (if a pipeline is associated) and auto_process is True
            logger.debug(f"Queuing documents for processing in vault '{vault_id}' with pipeline '{vault.pipeline_name}'")
            try:
                if vault.pipeline_name and vault.processing_config and vault.processing_config.auto_process_documents:
                    _queued_docs = await self.vault_document_service.queue_documents_for_processing(vault, _documents_uploaded)
                else:
                    logger.info(f"Vault '{vault_id}' has no associated pipeline or auto_process is disabled; skipping queuing documents for processing")
            except Exception as e:
                logger.error(f"Failed to queue or update documents for processing in vault '{vault_id}': {e}")
                logger.exception(e)
            
        # Continue even if queuing fails
        if _queued_docs and len(_queued_docs) > 0:
            return _queued_docs + _documents_failed
        else:
            return _documents_uploaded + _documents_failed
        
        
    async def add_document(self, vault_id: str, document: AddDocumentRequest) -> DocumentInfo:
        """Add a document to a vault (updates stats)"""
        vault = await self.get_vault(vault_id)
        if not vault:
            raise ValueError(f"Vault {vault_id} not found")

        if not document or not document.name or not document.blob_url:
            raise ValueError("Document with valid name and blob_url must be provided")
        
        logger.debug(f"Adding document '{document.name}' to vault '{vault_id}' from blob URL '{document.blob_url}'")
        
        # Add the document using the vault document service
        added_document = await self.vault_document_service.add_document(vault, document)
        
        # # Update stats
        # vault.stats = vault.stats or VaultStats()
        # vault.stats.total_documents += 1
        # vault.stats.total_size_bytes += added_document.size_bytes
        # if added_document.status == "processed":
        #     vault.stats.processed_documents += 1
        # elif added_document.status == "pending":
        #     vault.stats.pending_documents += 1
        # elif added_document.status == "failed":
        #     vault.stats.failed_documents += 1
        
        # vault.stats.last_activity = datetime.now(timezone.utc).isoformat()
        
        # vault.touch()
        # await self.update(vault.model_dump())
        
        return added_document


    async def remove_document(self, vault_id: str, document: DocumentInfo) -> bool:
        """Remove a document from a vault (updates stats)"""
        vault = await self.get_vault(vault_id)
        if not vault:
            return False

        # # Update stats
        # vault.stats.total_documents = max(0, vault.stats.total_documents - 1)
        # vault.stats.total_size_bytes = max(0, vault.stats.total_size_bytes - document.size_bytes)
        
        # if document.status == "processed":
        #     vault.stats.processed_documents = max(0, vault.stats.processed_documents - 1)
        # elif document.status == "pending":
        #     vault.stats.pending_documents = max(0, vault.stats.pending_documents - 1)
        # elif document.status == "failed":
        #     vault.stats.failed_documents = max(0, vault.stats.failed_documents - 1)

        # vault.touch()
        # await self.update(vault_id, vault.model_dump())
        return True


    async def get_vault_documents(self, vault_id: str) -> List[DocumentInfo]:
        """Get documents in a vault (placeholder - would typically query a separate documents collection)"""
        
        if not vault_id:
            raise ValueError("Vault ID must be provided")
        
        vault = await self.get_vault(vault_id)
        if not vault:
            raise ValueError(f"Vault {vault_id} not found")
        
        documents = await self.vault_document_service.get_vault_documents(vault_id)
        return documents


    async def process_vault(self, request: VaultProcessingRequest) -> dict:
        """Start processing documents in a vault"""
        vault = await self.get_vault(request.vault_id)
        if not vault:
            raise ValueError(f"Vault {request.vault_id} not found")

        
        # Here you would typically:
        # 1. Get documents to process
        # 2. Create batch execution request
        # 3. Submit to processing queue
        # For now, return a placeholder response
        
        return {
            "message": "Vault processing started",
            "vault_id": request.vault_id,
            "status": "processing",
            "documents_to_process": vault.stats.total_documents if not request.document_ids else len(request.document_ids)
        }


    async def check_pipeline_in_use_by_vault(self, pipeline_name: str) -> List[str]:
        """Check if a pipeline is used by any vault"""
        query = "SELECT * FROM c WHERE c.pipeline_name = @pipeline_name"
        parameters = [{"name": "@pipeline_name", "value": pipeline_name}]
        vaults_using_pipeline = await self.query(query=query, parameters=parameters)
        return [vault["name"] for vault in vaults_using_pipeline] if vaults_using_pipeline else []