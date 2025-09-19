from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
import fastapi

from app.models.vault import (
    AddDocumentRequest, UploadDocumentResponse, Vault, VaultCreateRequest, VaultUpdateRequest, VaultProcessingRequest,
    VaultStatus, DocumentInfo
)
from app.services.vault_service import VaultService
from app.dependencies import get_vault_service
from app.exceptions import ApiException

router = APIRouter(prefix="/api/vaults", tags=["vaults"])

################################################
## Vault management endpoints

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
        raise ApiException(status_code=400, message="Failed to create vault", details=str(e))
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to create vault", details=str(e))


@router.get("/", response_model=List[Vault])
async def list_vaults(
    service: VaultService = Depends(get_vault_service)
):
    """List all vaults with optional filtering"""
    try:
        vaults = await service.list_vaults()
        return vaults
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to list vaults", details=str(e))


@router.get("/{vault_id}", response_model=Vault)
async def get_vault(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Get a specific vault by ID"""
    try:
        vault = await service.get_vault(vault_id)
        if not vault:
            raise ApiException(status_code=404, message="Vault not found")
        return vault
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to get vault", details=str(e))


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
            raise ApiException(status_code=404, message="Vault not found")
        return vault
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to update vault", details=str(e))


@router.delete("/{vault_id}")
async def delete_vault(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Delete a vault"""
    try:
        success = await service.delete_vault(vault_id)
        if not success:
            raise ApiException(status_code=404, message="Vault not found")
        return {"message": "Vault deleted successfully"}
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to delete vault", details=str(e))


@router.get("/{vault_id}/status")
async def get_vault_status(
    vault_id: str,
    service: VaultService = Depends(get_vault_service)
):
    """Get vault processing status"""
    try:
        vault = await service.get_vault(vault_id)
        if not vault:
            raise ApiException(status_code=404, message="Vault not found")
        
        return {
            "vault_id": vault_id,
            "status": vault.status,
            "stats": vault.stats,
            "last_updated": vault.updated_at
        }
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to get vault status", details=str(e))


################################################
## Vault document management and processing endpoints

@router.post("/{vault_id}/upload", response_model=List[UploadDocumentResponse])
async def upload_documents_to_vault(
    vault_id: str,
    files: List[fastapi.UploadFile] = fastapi.File(...),
    overwrite: bool = fastapi.Form(default=False, description="Whether to overwrite existing documents with the same name"),
    service: VaultService = Depends(get_vault_service)
):
    """Upload documents to a vault"""
    try:
        result = []
        try:
            uploaded_docs = await service.add_uploaded_documents(vault_id, files, overwrite=overwrite)
            for doc in uploaded_docs:
                if isinstance(doc, dict) and doc.get("error"):
                    result.append(UploadDocumentResponse(
                        filename=doc.get("name", "unknown"),
                        document=None,
                        error=doc["error"]
                    ))
                else:
                    result.append(UploadDocumentResponse(
                        filename=doc.name,
                        document=doc,
                        error=None
                    ))
        except Exception as e:
            raise ApiException(status_code=500, message="Failed to upload documents", details=str(e))

        return result

    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to upload documents", details=str(e))


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
            raise ApiException(status_code=404, message="Vault not found")
        
        documents = await service.get_vault_documents(vault_id)
        return documents
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to get vault documents", details=str(e))


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
        raise ApiException(status_code=400, message="Invalid request", details=str(e))
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to start vault processing", details=str(e))


@router.post("/{vault_id}/add", response_model=List[DocumentInfo])
async def add_documents(
    vault_id: str,
    documents: List[AddDocumentRequest],
    service: VaultService = Depends(get_vault_service)
):
    """Add documents to a vault"""
    try:
        results = []
        
        for doc in documents:
            if not doc.name or not doc.blob_url:
                raise ApiException(status_code=400, message="Invalid document request data", details="Each document must have name and blob_url")
            result = await service.add_document(vault_id, doc)
            results.append(result)

        return results
    
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to add documents", details=str(e))


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
            raise ApiException(status_code=404, message="Vault not found")
        return {"message": "Document removed successfully"}
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message=f"Failed to remove document", details=str(e))



