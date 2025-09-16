from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends

from app.models.vault import (
    Vault, VaultCreateRequest, VaultUpdateRequest, VaultProcessingRequest,
    VaultStatus, DocumentInfo
)
from app.services.vault_service import VaultService
from app.dependencies import get_vault_service

router = APIRouter(prefix="/api/vaults", tags=["vaults"])

@router.post("/", response_model=Vault)
async def create_vault(
    request: VaultCreateRequest,
    service: VaultService = Depends(get_vault_service)
):
    """Create a new vault"""
    try:
        vault = await service.create_vault(request)
        return vault
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vault: {str(e)}")


@router.get("/", response_model=List[Vault])
async def list_vaults(
    status: Optional[VaultStatus] = None,
    limit: Optional[int] = 100,
    offset: int = 0,
    service: VaultService = Depends(get_vault_service)
):
    """List all vaults with optional filtering"""
    try:
        vaults = await service.list_vaults(status=status, limit=limit, offset=offset)
        return vaults
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list vaults: {str(e)}")


@router.get("/{vault_id}", response_model=Vault)
async def get_vault(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Get a specific vault by ID"""
    try:
        vault = await service.get_vault(vault_id)
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")
        return vault
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vault: {str(e)}")


@router.put("/{vault_id}", response_model=Vault)
async def update_vault(
    vault_id: str,
    request: VaultUpdateRequest,
    service: VaultService = Depends(get_vault_service)
):
    """Update a vault"""
    try:
        vault = await service.update_vault(vault_id, request)
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")
        return vault
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vault: {str(e)}")


@router.delete("/{vault_id}")
async def delete_vault(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Delete a vault"""
    try:
        success = await service.delete_vault(vault_id)
        if not success:
            raise HTTPException(status_code=404, detail="Vault not found")
        return {"message": "Vault deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete vault: {str(e)}")


@router.get("/{vault_id}/documents", response_model=List[DocumentInfo])
async def get_vault_documents(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Get documents in a vault"""
    try:
        # First check if vault exists
        vault = await service.get_vault(vault_id)
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")
        
        documents = await service.get_vault_documents(vault_id)
        return documents
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vault documents: {str(e)}")


@router.post("/{vault_id}/process")
async def process_vault(
    vault_id: str,
    document_ids: Optional[List[str]] = None,
    force_reprocess: bool = False,
    service: VaultService = Depends(get_vault_service)
):
    """Start processing documents in a vault"""
    try:
        request = VaultProcessingRequest(
            vault_id=vault_id,
            document_ids=document_ids,
            force_reprocess=force_reprocess
        )
        result = await service.process_vault(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start vault processing: {str(e)}")


@router.post("/{vault_id}/documents", response_model=dict)
async def add_document(
    vault_id: str,
    document: DocumentInfo,
    service: VaultService = Depends(get_vault_service)
):
    """Add a document to a vault"""
    try:
        success = await service.add_document(vault_id, document)
        if not success:
            raise HTTPException(status_code=404, detail="Vault not found")
        return {"message": "Document added successfully", "document_id": document.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@router.delete("/{vault_id}/documents/{document_id}")
async def remove_document(
    vault_id: str,
    document_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Remove a document from a vault"""
    try:
        # Create a minimal DocumentInfo for stats update
        # In a real implementation, you'd first fetch the document details
        document = DocumentInfo(
            id=document_id,
            name="unknown",
            size_bytes=0,
            content_type="unknown",
            upload_date="",
            status="unknown"
        )
        
        success = await service.remove_document(vault_id, document)
        if not success:
            raise HTTPException(status_code=404, detail="Vault not found")
        return {"message": "Document removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove document: {str(e)}")


@router.get("/{vault_id}/status")
async def get_vault_status(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Get vault processing status"""
    try:
        vault = await service.get_vault(vault_id)
        if not vault:
            raise HTTPException(status_code=404, detail="Vault not found")
        
        return {
            "vault_id": vault_id,
            "status": vault.status,
            "stats": vault.stats,
            "last_updated": vault.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vault status: {str(e)}")
