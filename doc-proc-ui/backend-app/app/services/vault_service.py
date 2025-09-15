from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone

from ..db.cosmos import CosmosDb
from ..models.vault import (
    Vault, VaultCreateRequest, VaultUpdateRequest, VaultProcessingRequest,
    VaultStatus, VaultStats, DocumentInfo
)
from .base import BaseService


class VaultService(BaseService):
    """Service for managing document vaults"""

    def __init__(self, db: CosmosDb):
        super().__init__(db, "vaults")

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate vault item"""
        required_fields = ["id", "name"]
        return all(field in item for field in required_fields)

    async def create_vault(self, request: VaultCreateRequest) -> Vault:
        """Create a new vault"""
        vault_id = f"vault_{uuid.uuid4().hex[:8]}"
        
        vault = Vault(
            id=vault_id,
            name=request.name,
            description=request.description,
            pipeline_id=request.pipeline_id,
            processing_config=request.processing_config or Vault.model_fields['processing_config'].default_factory(),
            azure_search_config=request.azure_search_config,
            storage_config=request.storage_config,
            stats=VaultStats()
        )
        
        saved_vault = await self.create(vault.model_dump())
        return Vault(**saved_vault)

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

    async def list_vaults(
        self, 
        status: Optional[VaultStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Vault]:
        """List vaults with optional filtering"""
        query = "SELECT * FROM c"
        parameters = []
        
        if status:
            query += " WHERE c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        query += " ORDER BY c.created_at DESC"
        
        if limit:
            query += f" OFFSET {offset} LIMIT {limit}"
        
        items = await self.query(query, parameters)
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

    async def add_document(self, vault_id: str, document: DocumentInfo) -> bool:
        """Add a document to a vault (updates stats)"""
        vault = await self.get_vault(vault_id)
        if not vault:
            return False

        # Update stats
        vault.stats.total_documents += 1
        vault.stats.total_size_bytes += document.size_bytes
        vault.stats.last_activity = datetime.now(timezone.utc).isoformat()
        
        if document.status == "processed":
            vault.stats.processed_documents += 1
        elif document.status == "pending":
            vault.stats.pending_documents += 1
        elif document.status == "failed":
            vault.stats.failed_documents += 1

        vault.touch()
        await self.update(vault_id, vault.model_dump())
        return True

    async def remove_document(self, vault_id: str, document: DocumentInfo) -> bool:
        """Remove a document from a vault (updates stats)"""
        vault = await self.get_vault(vault_id)
        if not vault:
            return False

        # Update stats
        vault.stats.total_documents = max(0, vault.stats.total_documents - 1)
        vault.stats.total_size_bytes = max(0, vault.stats.total_size_bytes - document.size_bytes)
        
        if document.status == "processed":
            vault.stats.processed_documents = max(0, vault.stats.processed_documents - 1)
        elif document.status == "pending":
            vault.stats.pending_documents = max(0, vault.stats.pending_documents - 1)
        elif document.status == "failed":
            vault.stats.failed_documents = max(0, vault.stats.failed_documents - 1)

        vault.touch()
        await self.update(vault_id, vault.model_dump())
        return True

    async def get_vault_documents(self, vault_id: str) -> List[DocumentInfo]:
        """Get documents in a vault (placeholder - would typically query a separate documents collection)"""
        # This would typically query a separate documents collection/container
        # For now, returning empty list as this would be implemented based on actual storage architecture
        return []

    async def process_vault(self, request: VaultProcessingRequest) -> dict:
        """Start processing documents in a vault"""
        vault = await self.get_vault(request.vault_id)
        if not vault:
            raise ValueError(f"Vault {request.vault_id} not found")

        # Update vault status to processing
        vault.status = VaultStatus.PROCESSING
        vault.touch()
        await self.update(request.vault_id, vault.model_dump())

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
