import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.services.base import BaseService
from app.db.cosmos import CosmosDb
from app.models.execution import BatchExecution, DocumentExecutionStatus, PipelineExecutionResult

logger = logging.getLogger("doc-proc-api.services.execution_status_service")
    
class ExecutionStatusService(BaseService):
    """Service for managing pipeline execution results operations"""

    def __init__(self, 
                 db: CosmosDb, 
                 pipeline_executions_container: str = "pipeline_executions",
                 vault_documents_container: str = "vault_documents",
                 batch_executions_container: str = "batch_executions",
                 ):
        super().__init__(db, "")
        
        self.pipeline_executions_container = pipeline_executions_container
        self.vault_documents_container = vault_documents_container
        self.batch_executions_container = batch_executions_container

    async def validate_item(self, item):
        return True  # No specific validation for now

    async def get_pipeline_execution_by_id(self, execution_id: str) -> Optional[PipelineExecutionResult]:
        """Get pipeline execution result by ID"""
        execution_data = await self.db.get(container=self.pipeline_executions_container, id=execution_id)
        return PipelineExecutionResult(**execution_data) if execution_data else None
    
    async def list_pipeline_executions(
        self, 
        batch_execution_id: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PipelineExecutionResult]:
        """List pipeline executions with optional filters"""
        where_conditions = []
        parameters = []
        
        if batch_execution_id:
            where_conditions.append("c.batch_execution_id = @batch_execution_id")
            parameters.append({"name": "@batch_execution_id", "value": batch_execution_id})
        
        if pipeline_name:
            where_conditions.append("c.pipeline_name = @pipeline_name")
            parameters.append({"name": "@pipeline_name", "value": pipeline_name})
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"""
        SELECT * FROM c 
        WHERE {where_clause} 
        ORDER BY c.created_at DESC 
        OFFSET {offset} LIMIT {limit}
        """
        
        execution_data = await self.query(query=query, parameters=parameters, container=self.pipeline_executions_container)
        return [PipelineExecutionResult(**execution) for execution in execution_data]
    
    async def get_pipeline_executions_by_batch(self, batch_execution_id: str) -> List[PipelineExecutionResult]:
        """Get all pipeline executions for a specific batch"""
        query = "SELECT * FROM c WHERE c.batch_execution_id = @batch_execution_id ORDER BY c.created_at DESC"
        parameters = [{"name": "@batch_execution_id", "value": batch_execution_id}]
        
        execution_data = await self.query(query=query, parameters=parameters, container=self.pipeline_executions_container)
        return [PipelineExecutionResult(**execution) for execution in execution_data]
    
    async def get_recent_pipeline_executions(self, pipeline_name: Optional[str] = None, limit: int = 20, time_range: Optional[str] = "last_24h") -> List[PipelineExecutionResult]:
        """Get recent pipeline executions within specified time range"""
        from datetime import timedelta
        
        # Calculate the cutoff datetime based on time_range
        now = datetime.now(timezone.utc)
        time_deltas = {
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        if time_range not in time_deltas:
            time_range = "24h"  # Default fallback

        cutoff_time = now - time_deltas[time_range]
        cutoff_timestamp = cutoff_time.isoformat()
        
        if pipeline_name:
            where_clause = "c.pipeline_name = @pipeline_name AND c.started_at >= @cutoff_time"
            parameters = [
                {"name": "@pipeline_name", "value": pipeline_name},
                {"name": "@cutoff_time", "value": cutoff_timestamp}
            ]
        else:
            where_clause = "c.started_at >= @cutoff_time"
            parameters = [{"name": "@cutoff_time", "value": cutoff_timestamp}]
        
        query = f"""
        SELECT * FROM c 
        WHERE {where_clause}
        ORDER BY c.started_at DESC
        OFFSET 0 LIMIT {limit}
        """
        
        execution_data = await self.query(query=query, parameters=parameters, container=self.pipeline_executions_container)
        return [PipelineExecutionResult(**execution) for execution in execution_data]
    
    async def get_pipeline_execution_stats(self, pipeline_name: Optional[str] = None) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        where_clause = ""
        parameters = []
        
        if pipeline_name:
            where_clause = "WHERE c.pipeline_name = @pipeline_name"
            parameters = [{"name": "@pipeline_name", "value": pipeline_name}]
        
        query = f"""
        select *
        from c
        {where_clause}
        """
        
        stats_data = await self.query(query=query, parameters=parameters, container=self.pipeline_executions_container)
        
        if not stats_data or not stats_data[0]:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "partial_succeessful_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time_secs": 0
            }
        
        stats = stats_data[0]
        total = stats.get("total_executions", 0)
        successful = stats.get("successful_executions", 0)
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": stats.get("failed_executions", 0),
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
            "avg_execution_time_secs": stats.get("avg_execution_time_secs", 0) or 0
        }
    
    
    async def delete_pipeline_execution_by_id(self, execution_id: str) -> bool:
        """Delete a pipeline execution result by ID"""
        return await self.delete(item_id=execution_id, container=self.pipeline_executions_container)


    async def get_batch_execution_by_id(self, batch_id: str) -> Optional[BatchExecution]:
        """Get batch execution by ID"""
        query = "SELECT * FROM c WHERE c.id = @batch_id"
        parameters = [{"name": "@batch_id", "value": batch_id}]
        
        batch_data = await self.query(query=query, parameters=parameters, container=self.batch_executions_container)
        return BatchExecution(**batch_data[0]) if batch_data else None


    async def get_batch_executions_count_for_vault(self, vault_id: str, status_filter: str) -> int:
        """Get count of batch executions associated with a specific vault, optionally filtered by status"""
        
        if not vault_id:
            raise ValueError("vault_id is required")
        
        if not status_filter or status_filter not in ['submitted', 'running', 'completed', 'failed', 'cancelled']:
            raise ValueError("status_filter must be one of 'submitted', 'running', 'completed', 'failed', 'cancelled'")
        
        
        where_conditions = ["c.vault_id = @vault_id"]
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        where_conditions.append("c.status = @status")
        parameters.append({"name": "@status", "value": status_filter})
        
        where_clause = " AND ".join(where_conditions)
        query = f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"

        count_data = await self.query(query=query, parameters=parameters, container=self.batch_executions_container)
        return count_data[0] if count_data else 0


    async def get_batch_executions_for_vault(self, vault_id: str, limit: int = 50, offset: int = 0) -> List[BatchExecution]:
        """Get batch executions associated with a specific vault"""
        query = f"""
        SELECT * FROM c 
        WHERE c.vault_id = @vault_id 
        ORDER BY c.created_at DESC 
        OFFSET {offset} LIMIT {limit}
        """
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        batch_data = await self.query(query, parameters, container=self.batch_executions_container)
        return [BatchExecution(**batch) for batch in batch_data]

    async def get_documents_execution_status(self, document_ids: List[str]) -> Optional[List[DocumentExecutionStatus]]:
        """Get execution status for a specific document across all batch executions"""
        
        # Get the batch ids associated with the documents from the vault_documents container
        _source_batch_ids_query = f"SELECT c.id, c.metadata.batch_id FROM c WHERE c.id IN ('{str.join("','", document_ids)}')"
        _doc_batch_id_pairs = await self.query(query=_source_batch_ids_query, container=self.vault_documents_container)

        if not _doc_batch_id_pairs or len(_doc_batch_id_pairs) == 0:
            return None  # None found
        
        query_template = f"""
        SELECT 
            d.id.unique_id as document_id,
            b.id as batch_id, 
            b.status as batch_status,
            b.pipeline_name,
            b.pipeline_execution_id,
            b.submitted_at as batch_submitted_at,
            b.started_at as batch_started_at,
            b.completed_at as batch_completed_at,
            b.metadata as batch_metadata,
            b.errors as batch_errors,
            d as document
            FROM batch_executions b 
            join d in b.documents 
            where 
            b.id = @batch_id AND
            d.id.unique_id = @document_id
        ORDER BY b.started_at ASC
        """
        
        # generate one query per document and batch id pair
        queries = []
        for doc in _doc_batch_id_pairs:
            if 'batch_id' in doc and doc['batch_id'] and 'id' in doc and doc['id']:
                queries.append((query_template, [{"name": "@batch_id", "value": doc['batch_id']}, {"name": "@document_id", "value": doc['id']}]))
        
        batch_executions = [self.query(query=query, parameters=params, container=self.batch_executions_container) for query, params in queries]
        batch_executions = await asyncio.gather(*batch_executions, return_exceptions=True)
        
        batch_executions = [item for sublist in batch_executions for item in sublist if not isinstance(item, Exception)]  # flatten list and filter out errors

        return [DocumentExecutionStatus(**batch) for batch in batch_executions]


    async def delete_batch_executions_for_vault(self, vault_id: str) -> bool:
        """Delete all batch executions associated with a specific vault."""
        if not vault_id:
            raise ValueError("vault_id is required")
        
        # 1. Delete all batch executions associated with the vault
        _be_query = "SELECT c.id FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        batch_executions = await self.query(query=_be_query, parameters=parameters, container=self.batch_executions_container)
        if not batch_executions:
            return True  # Nothing to delete

        delete_tasks = [self.delete(item_id=batch['id'], container=self.batch_executions_container) for batch in batch_executions]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # Check for exceptions
        for result in results:
            if isinstance(result, Exception):
                return False
        
        return True
    
    async def delete_pipeline_executions_for_vault(self, vault_id: str) -> bool:
        """Delete all pipeline executions associated with a specific vault"""
        if not vault_id:
            raise ValueError("vault_id is required")
        
        query = "SELECT c.id FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        pipeline_executions = await self.query(query, parameters, container=self.pipeline_executions_container)
        if not pipeline_executions:
            return True  # Nothing to delete

        delete_tasks = [self.delete(item_id=exec['id'], container=self.pipeline_executions_container) for exec in pipeline_executions]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # Check for exceptions
        for result in results:
            if isinstance(result, Exception):
                return False
        
        return True